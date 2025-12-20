# Monster Trucks!
The game can be run with
```bash
python monseter_truck.py
```

Right now, it's just a basic level, working on physics of the truck. The organization isn't great, but most things can be confugred in the config.py file for the levels and trucks.

Things I'd like to add:

- an end flag to complete the level on contact.
- a points system (tricks, airtime, flips)
- accumulative damage bar
  - less damage, more points
  - too much damage, explodes, game over
- starting screen with level/truck picker
- improved physics of truck
  - torque limiting as max wheel angular velocity is reached
  - top speed limiting
  - custom torque bands for different trucks
- additional level obstacles
  - physics obstacles like block walls, crumble bridges, etc.
  - improved method of setting different objects/sprites for the level
- score tracker