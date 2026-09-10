# Four-to-five minute submission demo

Use a real configured Rime session with synthetic appointment data.
This script distinguishes the working foundation from extensions still to build.

| Time | Demonstration |
| --- | --- |
| 0:00-0:35 | Explain the need: deliver appointment details when another voice may mask them. Rime supplies essential spoken output. |
| 0:35-1:35 | Run the working normal voice flow: hear time/location/reference, ask for a detail again, then give a fresh confirmation. |
| 1:35-2:20 | Show the grid's matched speech-noise example and aggregate evidence. Clean fact recovery is 94.90%; speech_2 at -5 dB is 17.35%. These are ASR proxy scores, not human listening results. Audio fixtures must be supplied before claiming this segment is ready. |
| 2:20-3:20 | After implementation and verification, demonstrate suspected competing speech blocking confirmation, a requested-detail replay and a correct fact read-back. Otherwise show the existing repeat flow and label the detector/read-back extension as unfinished. Never stage a detector result without disclosing injection. |
| 3:20-4:10 | Show the 294-row coverage and zero supported breakpoint result. Explain that 5 dB was an observed aggregate risk region for these recordings, not a general threshold. Show actual product acceptance counts only if collected. |
| 4:10-4:40 | Show active Rime configuration, architecture, reproduction instructions and limitations. Point to the evidence source and working code. |

Before recording: configure server-side credentials, run preflight, verify a live
session, make the noise evidence files accessible, and check the final screen
contains no secrets. A presentation of planned behavior is not a working
demonstration of that behavior. The final recording/link is still required.
