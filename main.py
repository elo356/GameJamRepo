from ursina import *

app = Ursina(title=" After Hours", size=(1280, 720))

piso = Entity(
    model="plane",               
    scale=(20, 1, 20),                
    texture=Texture("images/textures/floor.png", filtering=None), 
    texture_scale=(10, 10), 
    unlit=True,         
)

caja = Entity(model="cube", color=color.red, position=(0, 0.5, 5))

jugador = Entity(position=(0, 0, 0))
camera.parent = jugador               
camera.position = (0, 1.5, 0)         


def update():                        
    velocidad = 4 * time.dt           
    if held_keys["w"]:
        jugador.z += velocidad
    if held_keys["s"]:
        jugador.z -= velocidad
    if held_keys["d"]:
        jugador.x += velocidad
    if held_keys["a"]:
        jugador.x -= velocidad


app.run()