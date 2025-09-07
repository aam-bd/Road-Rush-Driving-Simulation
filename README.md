# Road-Rush-Driving-Simulation
### A 3D car combat and racing game built with Python and OpenGL. Drive through an infinite highway, combat enemy vehicles, and survive as long as possible while racking up points!

## 🚗 Game Features

### 🧭 3D Driving Experience
- Realistic vehicle movement with acceleration and lane changing

### 🔫 Combat System
- Fire at enemy vehicles using a mounted turret

### 🌗 Day/Night Cycle
- Dynamic lighting that transitions between day and night during gameplay

### 🎥 Multiple Camera Views
- Switch between third-person and first-person perspectives for immersive control

### 🤖 Enemy AI
- Intelligent opponents that attempt to block and attack your vehicle

### 💥 Visual Effects
- Includes explosions, muzzle flashes, and detailed environmental effects

### 🧾 HUD Display
- Real-time speedometer, distance tracker, score, and timer

## 🎮 Game Controls

| Action                           | Key         |
|----------------------------------|-------------|
| Accelerate                       | ↑ Up Arrow  |
| Brake / Reverse                  | ↓ Down Arrow|
| Change Lane Left                 | ← Left Arrow|
| Change Lane Right                | → Right Arrow|
| Fire Weapon                      | Spacebar    |
| Toggle Camera View               | V           |
| Increase Camera Height           | W           |
| Decrease Camera Height           | S           |
| Decrease Camera Distance         | A           |
| Increase Camera Distance         | D           |
| Advance Time (Day/Night)         | N           |
| Reverse Time (Day/Night)         | M           |
| Restart Game                     | R           |



## 🛠️ System Requirements

- Python 3.x
- PyOpenGL
- PyOpenGL-accelerate
- PyGame *(required for some installations)*
- FreeGLUT or a similar OpenGL utility library

  ## 🚀 Installation

Clone the repository:

```bash
https://github.com/aam-bd/Road-Rush-Driving-Simulation.git
cd road-rush
```

## 🚀 Installation

**No need to install any dependencies.

## 🎮 Gameplay

- Drive as far as possible while avoiding collisions with enemy vehicles  
- Shoot enemy cars and motorcycles to earn points  
- Collect health pickups by destroying enemies when your health is low  
- Manage your speed to navigate through traffic safely  
- Survive until time runs out to achieve the highest score  

---

## 🧮 Scoring System

- **Destroying enemy vehicles**: +200 points  
- **Distance traveled**: +0.2 points per unit of forward movement  
- **Firing weapon**: -1 point per shot *(encourages accuracy)*

## ⚙️ Technical Details

- Built with **Python** and **OpenGL** for 3D rendering  
- Uses **GLUT** for window management and input handling  
- Implements a **custom collision detection system**  
- Features **dynamic difficulty scaling** based on play time and distance  
- Includes **fog effects** for optimized rendering of distant objects

## 🙌 Acknowledgments

- Inspired by classic arcade racing games  
- Uses **OpenGL** and **GLUT** for graphics rendering  
- Thanks to the **PyOpenGL** community for their excellent library  
