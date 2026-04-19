# Maven

## Inspiration
With only 50% of U.S. adults considered financially literate, and less than 30% able to correctly answer the "Big Three" financial questions (interest, inflation, and risk diversification), there is a massive education gap. Because April is Financial Literacy Month, we were inspired to build a tactile, engaging platform to bridge this gap and make learning about personal finance accessible, intuitive, and fun.

## What it does
Maven is an arcade-style simulation game that teaches financial literacy through real-world, consequence-driven decision-making. Players navigate a dynamic financial journey where every choice, from weathering sudden expenses to transferring money between liquid cash and volatile investments, directly impacts their net worth. By simulating market rallies, losses, and savings growth, the game specifically tests players' practical understanding of the "Big Three" financial concepts in real-time.

## How we built it
We built Maven using a Raspberry Pi 4 running a custom Python and Pygame engine to handle the core financial simulation, state machine, and visual HUD. To create an immersive, arcade-like experience, we wired a 4x4 membrane keypad directly to the Pi’s GPIO pins, writing custom debounce logic to accurately handle user inputs for fund transfers and game navigation. We also integrated a multi-sensory feedback system using indicator LEDs and a passive tonal buzzer, physically syncing audio-visual cues with the player's in-game financial gains and losses. Ultimately, by seamlessly bridging low-level hardware interrupts with a responsive software loop, we transformed abstract financial concepts into a tangible arcade game.

## Challenges we ran into
We had difficulty connecting the Raspberry Pi 4 to the Wi-Fi. The main reason for this is that we did not have an external monitor, keyboard, or mouse. We had to do research on the "handless" setup, where we force the Raspberry Pi to connect to one of our laptops' hotspots so we can then perform screen sharing and provide SSH access. The game design was also challenging, mainly because the simulation of financial systems is complex and involves many factors. Trying to do that while working with Raspberry Pi's for the first time was a lot more difficult than anticipated.

## Accomplishments that we're proud of
We are very proud that we were able to finish this prototype and proof-of-concept while having no extensive experience with Raspberry Pi's. Being able to create this project that helps the community of people who struggle to manage their finances in just 24 hours is really satisfying.

## What we learned
We learned a lot from this project. To start off, we learned a lot about networking just to connect to the Raspberry Pi from a project where all the logic is done on board! It just shows how surprising these projects can get. From there, we learned how to work with PyGame and utilize Python for game development. Lastly, we also learned how to tell if a buzzer is active or passive. Overall, we learned a lot from this project in just one day. 

## What's next for Maven
In the future, we hope to develop Maven so we can take this from a prototype and proof-of-concept to a final product. As seen in the image gallery, we had developed an arcade-like housing using CAD. However, there wasn't enough time to have it 3D-printed, so we will have to do it in the future. From there, we hope to improve the game and simulation so that they are more accurate, have better functionality, and offer more customization. For instance, taking into account inflation, unemployment, salary changes, different investment methods, and different ways of paying (e.g., credit cards) are all financial aspects that would make this game a lot more immersive and would allow the user to personalize the game to simulate their current situation.
