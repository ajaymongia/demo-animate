Animate this SVG illustration and give me a Lottie JSON and an animated SVG of it.

Illustration: [attach the .svg or give its path]
Name: [e.g. "Onboarding Robot"]
Motion idea (optional): [e.g. "cursor clicks the robot, robot waves", or leave blank and propose one]

What I need
1. motion-kit.json: a Lottie file (bodymovin 5.7 schema) that plays in lottie-web, lottie-ios and lottie-android.
2. motion-kit.svg: the same animation as a standalone SVG that animates by itself, including when used in an <img> tag.
3. motion-kit-preview.html: one standalone file that plays both side by side.
4. A preview page called "[Name]" showing the SVG and the Lottie side by side, with three download buttons: Lottie (.json), SVG (.svg) and Preview (.html). Nothing else on the page.

How to animate it
- Study the artwork first and work out its parts: background, shadows, panels, the main character or object, small details such as eyes, hands, buttons, and any cursor or pointer.
- Plan one short story: a calm idle loop (gentle floating, parallax between layers, shadows that shrink as things rise) plus one main moment (for example a click, a reaction, a wave or a blink). Keep it tasteful and on-brand, not busy.
- Use a 4-second seamless loop at 60 fps (240 frames). The first and last frames must match so the loop has no jump.
- Ease everything: in-out for floating, a small overshoot for pops, a quick settle after impacts. No linear motion except holds.
- Keep the original shapes, colours and gradients exactly as drawn. Only group them and move them. Small extras such as click ripples or sparkles are fine if they fit the style.

How to build it
- Write one motion spec (groups, pivot points, keyframes, easing) and generate BOTH the SVG and the Lottie from it with a script, so they always match. Keep that script so we can tweak timings and rebuild.
- SVG: wrap each moving part in a <g>, animate it with CSS keyframes inside the file (translate, rotate, scale, opacity, with transform-origin at the part's pivot), and pause the animation for people who have reduced motion turned on.
- Lottie: one shape layer with nested groups that mirror the SVG groups. Convert every path, including multi-part paths. Support solid fills, linear and radial gradients (elliptical radial gradients too), gradient strokes, stroke width, round caps and joins, and element opacity. Do not use expressions, masks, images or fonts. Add named markers for the main beats (for example "click", "react", "blink").

Before you hand it over
- Render both in a browser and compare them at several key frames (start, the main moment, a blink or reaction). They must look identical and there must be no console errors.
- Tell me the file sizes, what moves and when (a short beat-by-beat list), and anything you could not check.
