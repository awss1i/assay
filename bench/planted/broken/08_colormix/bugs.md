1.
- **What changed:** In `componentToHex`, the zero-pad guard is now `hex.length < 1 ? '0' + hex : hex`; it was `hex.length == 1 ? '0' + hex : hex`, which padded one-digit values like `f` to `0f`.
- **What goes wrong:** Whenever a color channel is 15 or less, the hex string comes out the wrong length, so the browser parses it as a different color and the swatch shows the wrong hue.
- **How to see it:** On a freshly loaded page, set the Green slider to 15; the swatch turns bright green (#00FF00) instead of the near-black dark green (#000F00) that value should produce.

2.
- **What changed:** In `updateColor`, the blue readout line is now `blueVal.textContent = g;`; it was `blueVal.textContent = b;`.
- **What goes wrong:** The Blue number next to the slider displays the green channel's value instead of the blue channel's value.
- **How to see it:** On a freshly loaded page, drag the Green slider to about 100 while leaving the Blue slider at 0; the "Blue:" readout shows 100.

3.
- **What changed:** The first listener is now `redVal.addEventListener('input', updateColor);`; it was `red.addEventListener('input', updateColor);`, attached to the red slider.
- **What goes wrong:** Dragging the red slider does nothing at all, because the handler is on the label span, which never emits input events; the red channel has no effect on the color.
- **How to see it:** On a freshly loaded page, drag the Red slider to the right; the swatch stays black, while the Green and Blue sliders still change the color normally.

4.
- **What changed:** In `updateColor`, the line `hexCode.value = hex;` was removed; it previously assigned the new hex string to the hex code field on every color update.
- **What goes wrong:** The hex code in the output field is never redrawn, so it is frozen at its initial value no matter what the user mixes.
- **How to see it:** On a freshly loaded page, drag the Green slider all the way to the right; the swatch becomes bright green but the Hex field still reads #000000.

5.
- **What changed:** In the Copy button's click handler, the order is now `document.execCommand('copy');` followed by `hexCode.select();`; it was `hexCode.select();` followed by `document.execCommand('copy');`.
- **What goes wrong:** The copy command runs before the hex field is selected, so the clipboard never receives the hex code.
- **How to see it:** On a freshly loaded page, click Copy, then press Ctrl+V (Cmd+V) in the browser address bar or any empty text field; no hex code is pasted because nothing was selected when the copy ran.