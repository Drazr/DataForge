"""Pure conversation policy. No provider, transport, or dataset dependencies."""
from __future__ import annotations

import re
import math
import time
from dataclasses import asdict, dataclass
from typing import Literal, Protocol
from .facts import matches_fact

IntentName = Literal['confirm', 'reject', 'repeat', 'stop', 'unclear', 'difficulty']
DETAILS = ('time', 'location', 'reference')
CHECKED_FACTS = ('reference', 'time')


@dataclass(frozen=True)
class Appointment:
    title: str = 'Community studio visit'
    date: str = '18 September 2026'
    time: str = '9:20 AM'
    timezone: str = 'India Standard Time'
    location: str = 'Riverside Community Studio'
    reference: str = 'DF 4821'


@dataclass(frozen=True)
class Intent:
    name: IntentName
    detail: str | None = None


@dataclass(frozen=True)
class Context:
    status: str
    last_detail: str
    confirmation_ready: bool


class IntentInterpreter(Protocol):
    def interpret(self, transcript: str, context: Context) -> Intent: ...


class GuidedInterpreter:
    """Full utterance matching prevents a stray 'yes' from authorizing action."""
    def interpret(self, transcript: str, context: Context) -> Intent:
        text = re.sub(r'[^a-z0-9\s]', '', transcript.lower())
        text = ' '.join(text.split())
        text = re.sub(r'^(please |could you |can you )', '', text)
        text = re.sub(r' please$', '', text)
        if text in {'yes', 'yes please', 'yes i confirm', 'i confirm', 'confirm',
                    'yes that works', 'that works', 'yes thats correct'}:
            return Intent('confirm')
        if text in {'no', 'no thank you', 'i cant attend', 'i cannot attend', 'that doesnt work'}:
            return Intent('reject')
        if text in {'stop', 'end the session', 'goodbye', 'cancel', 'stop talking'}:
            return Intent('stop')
        if text in {'i hear another voice', 'there is another voice', 'too noisy',
                    'i cant hear you', 'i cannot hear you', 'someone else is speaking'}:
            return Intent('difficulty')
        if text in {'repeat', 'repeat that', 'say that again', 'repeat the last detail',
                    'i didnt hear that', 'pardon'}:
            return Intent('repeat', context.last_detail)
        for detail, names in {'time': ('time', 'date', 'date and time'),
                              'reference': ('code', 'reference', 'reference code'),
                              'location': ('location', 'address')}.items():
            for name in names:
                if text in {f'repeat the {name}', f'say the {name} again',
                            f'what is the {name}', f'whats the {name}'}:
                    return Intent('repeat', detail)
        return Intent('unclear')


def make_interpreter(name: str = 'guided') -> IntentInterpreter:
    if name != 'guided':
        raise ValueError('Only the guided interpreter is installed; LLM support is deferred.')
    return GuidedInterpreter()


@dataclass(frozen=True)
class Segment:
    id: str
    text: str
    fact_id: str | None = None


class DeliveryPlanner:
    version = 'plain-v1'

    def __init__(self, appointment: Appointment):
        self.appointment = appointment

    def detail(self, detail: str) -> Segment:
        a = self.appointment
        texts = {
            'time': f'Your appointment is on {a.date}, at {a.time}, {a.timezone}.',
            'location': f'The location is {a.location}.',
            'reference': 'Your reference code is ' + ', '.join(a.reference.replace(' ', '')) + '.',
        }
        return Segment(detail, texts[detail], detail)

    def question(self) -> Segment:
        return Segment('question', 'Can you confirm this appointment? Say yes, no, or ask me to repeat a detail.')

    def readback(self, fact: str) -> Segment:
        requests = {'reference': 'Please say the full reference code, including its letters.',
                    'time': 'Please say the appointment time, including A M or P M.'}
        return Segment('readback_' + fact, requests[fact])


class Controller:
    """Only this controller can acknowledge an appointment.

    generation invalidates callbacks. Input timestamps refer to speech onset,
    not transcript arrival, so late ASR results cannot confirm early speech.
    """
    def __init__(self, appointment: Appointment | None = None,
                 interpreter: IntentInterpreter | None = None, clock=time.monotonic):
        self.appointment = appointment or Appointment()
        self.planner = DeliveryPlanner(self.appointment)
        self.interpreter = interpreter or make_interpreter()
        self.clock = clock
        self.status = 'ready'
        self.confirmed = False
        self.last_detail = 'time'
        self.current: Segment | None = None
        self.generation = 0
        self.ready_at: float | None = None
        self.unanswered = 0
        self.events: list[dict] = []
        self.seen_inputs: set[str] = set()
        self.failure: str | None = None
        self.verified_facts: set[str] = set()
        self.fact_check_required = False
        self.pending_fact: str | None = None
        self.fact_attempts = 0
        self.speech_risk = {'state': 'not_assessed', 'source': 'detector_unavailable',
                            'detector_installed': False}
        self.emit('created')

    def emit(self, event: str, **fields):
        self.events.append({'schema': 1, 'seq': len(self.events), 'at': self.clock(),
                            'event': event, 'turn': self.generation, **fields})

    @property
    def terminal(self):
        return self.status in {'confirmed', 'ended'}

    def snapshot(self):
        return {'status': self.status, 'confirmed': self.confirmed,
                'turn': self.generation,
                'current_text': self.current.text if self.current else '',
                'failure': self.failure, 'appointment': asdict(self.appointment),
                'pending_fact': self.pending_fact,
                'verified_facts': sorted(self.verified_facts),
                'fact_check_required': self.fact_check_required,
                'speech_risk': dict(self.speech_risk)}

    def next_question(self):
        if not self.fact_check_required:
            return self.planner.question()
        missing = next((fact for fact in CHECKED_FACTS if fact not in self.verified_facts), None)
        return self.planner.readback(missing) if missing else self.planner.question()

    def details(self):
        return [self.planner.detail(d) for d in DETAILS]

    def start(self):
        if self.status != 'ready':
            return []
        self.status = 'active'
        self.emit('started')
        return [Segment('welcome', 'Let us confirm your practice appointment. Please wait for the question before replying.')] + self.details() + [self.next_question()]

    def begin(self, segment: Segment, generation: int) -> bool:
        if generation != self.generation or self.status == 'recovery':
            return False
        self.current = segment
        self.ready_at = None
        if segment.fact_id:
            self.last_detail = segment.fact_id
        self.emit('segment_started', segment=segment.id)
        return True

    def complete(self, segment: Segment, generation: int) -> bool:
        if generation != self.generation or self.current != segment:
            return False
        self.current = None
        if segment.id == 'question':
            self.ready_at = self.clock()
            self.status = 'awaiting_confirmation'
            self.pending_fact = None
        elif segment.id in {'readback_reference', 'readback_time'}:
            self.ready_at = self.clock()
            self.pending_fact = segment.id.removeprefix('readback_')
            self.status = 'awaiting_fact'
        self.emit('playback_complete', segment=segment.id)
        return True

    def reset_playback(self):
        self.current = None
        self.generation += 1
        self.ready_at = None
        self.pending_fact = None
        if not self.terminal and self.status != 'recovery':
            self.status = 'active'

    def receive(self, transcript: str, input_id: str, started_at: float):
        if self.terminal or self.status not in {'awaiting_confirmation', 'awaiting_fact'} or self.current or input_id in self.seen_inputs:
            return []
        self.seen_inputs.add(input_id)
        context = Context(self.status, self.last_detail, self.ready_at is not None)
        try:
            intent = self.interpreter.interpret(transcript, context)
        except Exception:
            intent = None
        if (not isinstance(intent, Intent) or intent.name not in {'confirm', 'reject', 'repeat', 'stop', 'unclear', 'difficulty'}
                or (intent.name == 'repeat' and intent.detail not in DETAILS)
                or (intent.name != 'repeat' and intent.detail is not None)):
            intent = Intent('unclear')
            self.emit('invalid_interpreter_output')
        eligible = (self.ready_at is not None and isinstance(started_at, (int, float))
                    and not isinstance(started_at, bool) and math.isfinite(started_at)
                    and started_at >= self.ready_at)
        pending_fact = self.pending_fact
        self.emit('intent', intent=intent.name, detail=intent.detail, eligible=eligible)
        if intent.name == 'difficulty':
            return self.report_difficulty('user_reported')
        self.reset_playback()
        if intent.name in {'reject', 'stop'}:
            self.status = 'ended'
            self.emit('ended', reason=intent.name)
            return [Segment('ended', 'The session has ended. Your appointment has not been confirmed.')]
        if not eligible:
            self.emit('input_rejected', reason='not_fresh')
            return [self.next_question()]
        if intent.name == 'repeat':
            self.unanswered = 0
            repeat = self.planner.detail(intent.detail)
            if intent.detail in CHECKED_FACTS:
                self.verified_facts.discard(intent.detail)
                self.fact_attempts = 0
            return [repeat, self.next_question()]
        if pending_fact:
            matched = matches_fact(pending_fact, transcript, self.appointment)
            self.emit('fact_readback', fact=pending_fact, matched=matched,
                      source='recognized_reply', raw_transcript_retained=False)
            if matched:
                self.verified_facts.add(pending_fact)
                self.fact_attempts = 0
                if set(CHECKED_FACTS) <= self.verified_facts:
                    self.speech_risk = {**self.speech_risk, 'state': 'addressed_by_readback'}
                    self.emit('speech_risk_addressed', method='critical_fact_readback')
                return [self.next_question()]
            self.fact_attempts += 1
            if self.fact_attempts >= 2:
                self.status = 'ended'
                self.emit('ended', reason='fact_not_verified', fact=pending_fact)
                return [Segment('ended', 'I could not verify that detail. Your appointment remains unconfirmed. Please check the details on screen.')]
            return [Segment('fact_mismatch', 'That did not match the detail. Please listen and say it back after the question.'),
                    self.planner.detail(pending_fact), self.next_question()]
        if intent.name == 'confirm' and (not self.fact_check_required or
                                         set(CHECKED_FACTS) <= self.verified_facts):
            self.confirmed = True
            self.status = 'confirmed'
            self.emit('confirmed')
            return [Segment('acknowledgment', 'Thank you. Your practice appointment is confirmed. No real booking has been changed.')]
        self.unanswered += 1
        if self.unanswered >= 2:
            self.status = 'ended'
            self.emit('ended', reason='unanswered')
            return [Segment('ended', 'I could not get a clear confirmation. Your appointment remains unconfirmed. Goodbye.')]
        return [Segment('clarify', 'Please say yes to confirm, no, or ask me to repeat the time or code.'), self.next_question()]

    def report_difficulty(self, source='user_reported'):
        if source not in {'user_reported', 'demo_injected'}:
            raise ValueError('Unsupported speech-risk source.')
        if self.terminal or self.status in {'ready', 'recovery'}:
            raise ValueError('Start or recover the voice session before reporting difficulty.')
        self.reset_playback()
        self.verified_facts.clear()
        self.fact_check_required = True
        self.fact_attempts = 0
        self.speech_risk = {'state': 'suspected', 'source': source,
                            'detector_installed': False, 'reported_at': self.clock()}
        self.emit('speech_risk_reported', **self.speech_risk)
        self.emit('fact_checks_reset', reason='reported_speech_risk')
        return [Segment('speech_risk', 'You reported difficulty hearing. Please move somewhere quieter if you can. Let us check the code and time again.')] + self.details() + [self.next_question()]

    def fail(self, category: str):
        if self.terminal:
            self.emit('post_outcome_failure', category=category)
            return
        self.reset_playback()
        self.verified_facts.clear()
        self.fact_attempts = 0
        self.status = 'recovery'
        self.failure = category
        self.emit('failure', category=category)

    def recover(self):
        if self.status != 'recovery':
            return []
        self.failure = None
        self.status = 'active'
        self.emit('recovered')
        return self.details() + [self.next_question()]

    def end(self):
        self.reset_playback()
        if not self.confirmed:
            self.status = 'ended'
        self.emit('ended', reason='session_closed')
