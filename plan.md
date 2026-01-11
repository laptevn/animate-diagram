You create command line application that animate software diagram.
Animation is only for arrows that represent data flows.

Inputs:
- path to diagram SVG file

Outputs:
- created GIF file with animated diagram.

Todo:
1. Identify arrows on provided diagram.
2. Identify a direction of each arrow.
3. Use CSS to automate arrows in this diagram. You may need to create several frames.
4. Combine frames into GIF.

Hints:
1. Do not touch any elements on a diagram except arrows.
2. Make simple changes in iterations, don't do major refactorings.
3. Verify each change.
4. Fix problems by resolving root causes.
5. Use Python for CLI
6. Make it standard Python project that can be built to get all required dependencies.
7. You can use "example.svg" file as example of input for writing code.

Verification:
1. Compare result GIF and source SVG - only arrows should be changed.
You may compare components of one frame in result GIF for this.