"""Pure conversation policy. No provider, transport, or dataset dependencies."""
from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass
from typing import Literal, Protocol

IntentName = Literal['confirm', 'reject', 'repeat', 'stop', 'unclear']
DETAILS = ('time', 'location', 'reference')


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
        self.progress = dict.fromkeys(DETAILS, 'pending')
        self.last_detail = 'time'
        self.current: Segment | None = None
        self.generation = 0
        self.ready_at: float | None = None
        self.unanswered = 0
        self.events: list[dict] = []
        self.seen_inputs: set[str] = set()
        self.failure: str | None = None
        self.emit('created')

    def emit(self, event: str, **fields):
        self.events.append({'schema': 1, 'seq': len(self.events), 'at': self.clock(),
                            'event': event, 'turn': self.generation, **fields})

    @property
    def terminal(self):
        return self.status in {'confirmed', 'ended'}

    def snapshot(self):
        return {'status': self.status, 'confirmed': self.confirmed,
                'progress': dict(self.progress), 'turn': self.generation,
                'current_text': self.current.text if self.current else '',
                'failure': self.failure, 'appointment': asdict(self.appointment)}

    def remaining(self):
        return [self.planner.detail(d) for d in DETAILS if self.progress[d] != 'complete']

    def start(self):
        if self.status != 'ready':
            return []
        self.status = 'active'
        self.emit('started')
        return [Segment('welcome', 'Let us confirm your practice appointment. You can interrupt or ask me to repeat any detail.')] + self.remaining() + [self.planner.question()]

    def begin(self, segment: Segment, generation: int) -> bool:
        if generation != self.generation or self.status == 'recovery':
            return False
        self.current = segment
        self.ready_at = None
        if segment.fact_id:
            self.progress[segment.fact_id] = 'playing'
            self.last_detail = segment.fact_id
        self.emit('segment_started', segment=segment.id)
        return True

    def complete(self, segment: Segment, generation: int) -> bool:
        if generation != self.generation or self.current != segment:
            return False
        if segment.fact_id:
            self.progress[segment.fact_id] = 'complete'
        self.current = None
        if segment.id == 'question' and all(p == 'complete' for p in self.progress.values()):
            self.ready_at = self.clock()
            self.status = 'awaiting_confirmation'
        self.emit('playback_complete', segment=segment.id)
        return True

    def interrupt(self):
        if self.current and self.current.fact_id:
            self.progress[self.current.fact_id] = 'pending'
        self.current = None
        self.generation += 1
        self.ready_at = None
        if not self.terminal and self.status != 'recovery':
            self.status = 'listening'
        self.emit('interrupted')

    def receive(self, transcript: str, input_id: str, started_at: float):
        if self.terminal or self.status in {'ready', 'recovery'} or input_id in self.seen_inputs:
            return []
        self.seen_inputs.add(input_id)
        context = Context(self.status, self.last_detail, self.ready_at is not None)
        try:
            intent = self.interpreter.interpret(transcript, context)
        except Exception:
            intent = None
        if (not isinstance(intent, Intent) or intent.name not in {'confirm', 'reject', 'repeat', 'stop', 'unclear'}
                or (intent.name == 'repeat' and intent.detail not in DETAILS)
                or (intent.name != 'repeat' and intent.detail is not None)):
            intent = Intent('unclear')
            self.emit('invalid_interpreter_output')
        eligible = self.ready_at is not None and started_at >= self.ready_at
        self.emit('intent', intent=intent.name, detail=intent.detail, eligible=eligible)
        self.interrupt()
        if intent.name in {'reject', 'stop'}:
            self.status = 'ended'
            self.emit('ended', reason=intent.name)
            return [Segment('ended', 'The session has ended. Your appointment has not been confirmed.')]
        if intent.name == 'confirm' and eligible and all(p == 'complete' for p in self.progress.values()):
            self.confirmed = True
            self.status = 'confirmed'
            self.emit('confirmed')
            return [Segment('acknowledgment', 'Thank you. Your practice appointment is confirmed. No real booking has been changed.')]
        if intent.name == 'repeat':
            self.unanswered = 0
            repeat = self.planner.detail(intent.detail)
            return [repeat] + [s for s in self.remaining() if s.fact_id != intent.detail] + [self.planner.question()]
        self.unanswered += 1
        if self.unanswered >= 2:
            self.status = 'ended'
            self.emit('ended', reason='unanswered')
            return [Segment('ended', 'I could not get a clear confirmation. Your appointment remains unconfirmed. Goodbye.')]
        return [Segment('clarify', 'Please listen to the remaining details, then say yes to confirm, no, or ask me to repeat the time or code.')] + self.remaining() + [self.planner.question()]

    def fail(self, category: str):
        if self.terminal:
            self.emit('post_outcome_failure', category=category)
            return
        self.interrupt()
        self.status = 'recovery'
        self.failure = category
        self.emit('failure', category=category)

    def recover(self):
        if self.status != 'recovery':
            return []
        self.failure = None
        self.status = 'active'
        self.emit('recovered')
        return self.remaining() + [self.planner.question()]

    def end(self):
        self.interrupt()
        if not self.confirmed:
            self.status = 'ended'
        self.emit('ended', reason='session_closed')
