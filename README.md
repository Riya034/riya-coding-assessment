# Riya Coding Practice Platform

This is a locally hosted **independent practice interface** inspired by the layout of the reference screenshots. It is not an official Mercer Mettl assessment or affiliated with Mercer Mettl.

## Start the functional assessment

1. Install **Python 3** and **JDK 17 or newer** (both `java` and `javac` should be available on PATH).
2. Extract the ZIP, then open a terminal in the `riya_assessment` folder.
3. Run `py server.py` on Windows (or `python server.py` if that command is available).
4. Open **http://localhost:8000** in your browser.

To see the interface only, open `index.html` directly. For the **Compile and Test** button to work, the local server must be running.

## Contents
- `index.html`: Riya-named assessment interface, five questions, Java editor, navigation, running timer, save/submit/revisit buttons, and detailed test results.
- `server.py`: local Java 17 compilation and execution harness supporting all five questions.

## Important teacher information
- The runner compiles and executes **user-entered Java code**. Use it **only on a trusted local machine** for testing. It is not securely sandboxed for unknown students or the public internet.
- For remote student access, run this through a secure, isolated code execution service with authentication, per-run isolation, strict time/memory/network limits, and a real storage backend. **Do not expose this server on a public host.**
- Submissions are saved in each browser's local storage; they are not sent to the instructor. Students must submit/export their solutions separately.
- The countdown is local and resets on reload; it does not enforce a real examination deadline.
- Sample tests run from the server. The interface does not claim official assessment scoring.

Final screen: after the summary drawer, confirm Finish Assessment to see the completion and feedback page. Feedback is saved in this browser only.
