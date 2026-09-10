# Four-to-five minute submission demo

Use a real configured Rime session with synthetic appointment data.
All implementation shown must come from the `final-product` branch.

| Time | Demonstration |
| --- | --- |
| 0:00-0:35 | Explain the need: deliver appointment details when another voice may mask them. Rime supplies essential spoken output. |
| 0:35-1:35 | Run the working normal voice flow: hear time/location/reference, ask for a detail again, then give a fresh confirmation. |
| 1:35-2:20 | Play the supplied `critical_01` clean and speech_2 −5 dB pair. The selected clean clip recovered all 7 facts; the −5 dB clip recovered 0/7 and followed background speech. Label these saved ASR proxies, not human listening results. |
| 2:20-3:20 | Select **Hearing another voice?**. Show that “yes” cannot confirm until the caller reads back reference `DF 4821` and time `9:20 AM`; then complete a correct read-back. State that the trigger is user-reported, not an automatic detector. |
| 3:20-4:10 | Show the 294-row coverage and zero supported breakpoint result. Explain that 5 dB was an observed aggregate risk region for these recordings, not a general threshold. Show actual product acceptance counts only if collected. |
| 4:10-4:40 | Show active Rime configuration, architecture, reproduction instructions and limitations. Point to the evidence source and working code. |

Before recording: configure server-side credentials, run preflight and the focused
live suite, verify that received audio and redacted events were saved, and check
the screen contains no secrets. Put the final URL in `DEMO_LINK.md` and README.
