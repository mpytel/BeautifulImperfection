# Beautiful Imperfection

A fractal-based game exploring the balance between love and logic, where players build complex structures from simple elements.

A possible framework to gameafy experiments of social interactions as civilization levels up.

## Game Concept

Beautiful Imperfection is a game about finding harmony in imperfection. Players create fractal structures by connecting and evolving elements, balancing the opposing forces of love and logic to create something beautiful.

### Core Philosophy

- **Life is love or logic**: Never both simultaneously, but a mix at any instance. This imperfect mixture is most beautiful because it rises to a noticeable instance.
- **Steps for perfection**: Proof then modify. To evolve a perfect instance of anything involves iteration of these steps to the point of diminishing return.
- **Finding miracles in the ordinary**: The crux is dealing with the finer details, both in micro and in refinement. Shallow understanding of nature leads to invisible paths. A depth in understanding is leadership in direction.

## Gameplay

Players start with basic elements and must:
1. Connect elements to form relationships
2. Balance the love/logic ratio of each element
3. Evolve elements to higher forms
4. Create new child elements that inherit properties from their parents
5. Build complex fractal structures where lower levels support higher ones
6. Change element shapes to create visual variety
7. Complete levels to build increasingly complex fractal structures

## Controls

- **Mouse**: Click to select elements, drag to move them
- **Click Sequence**: Click one element then another to connect/disconnect them
- **Up/Down Arrow Keys**: Adjust love/logic balance of selected element
- **Space**: Evolve selected element
- **S**: Change the shape of the selected element
- **C**: Create a child element from selected element
- **Z**: Undo last action
- **R**: Restart game (with confirmation)
- **M**: Toggle background music on/off
- **COMPLETE Button**: Finish the current level and advance to the next (requires reaching target harmony)
- **ESC**: Quit the game

## Visual Elements

- **Colors**:
  - Love is represented by orange
  - Logic is represented by blue
  - Perfect balance is represented by green

- **Shapes**:
  - Circle, Square, Star, Hexagon, Pentagon
  - Triangle, Diamond, Cross, Heart, Crescent

## Level Progression

1. **Level 1**: Start with a single element and build your first structure
2. **Level 2**: Your level 1 structure becomes embedded in two larger elements
3. **Higher Levels**: Each level incorporates the previous level's structure as components

The game preserves the fine details of lower-level structures when they're displayed in higher levels, maintaining their original colors and shapes while using the current level's harmony to color the connections between them.

## Requirements

- Python 3
- Pygame library

## Running the Game

```
python3 beautiful_imperfection.py
```

## Features

- **Drag and Drop**: Intuitive element manipulation
- **Shape Changing**: 10 different shapes to choose from
- **Fractal Structures**: Each level builds upon the previous one
- **Harmony Meter**: Visual feedback on the balance of your creation
- **Image Saving**: Completed levels are saved as images with timestamps
- **Inheritance**: Child elements inherit properties from their parents
- **Visual Preservation**: Lower-level structures maintain their visual properties in higher levels
- **Dynamic Music**: Background music that adjusts volume based on harmony score

## Future Development Ideas

- Sound effects and music that reflect the love/logic balance
- More complex fractal patterns and behaviors
- Additional gameplay mechanics based on the philosophical concepts
- Visual effects that represent the beauty of imperfection
- Saving and sharing created fractal structures
- Multiplayer collaborative creation
