import arcade
import math
import random

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Campo de Visão (FOV)"

class Player(arcade.SpriteSolidColor):
    """Classe que representa e controla o jogador."""
    def __init__(self):
        super().__init__(30, 30, (100, 150, 255))
        self.color = (100, 150, 255)
        self.MOVEMENT_SPEED = 5
        
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False

    def update_movement(self):
        """Atualiza o vetor de velocidade baseado nas teclas pressionadas."""
        self.change_x = 0
        self.change_y = 0

        if self.up_pressed and not self.down_pressed:
            self.change_y = self.MOVEMENT_SPEED
        elif self.down_pressed and not self.up_pressed:
            self.change_y = -self.MOVEMENT_SPEED
            
        if self.left_pressed and not self.right_pressed:
            self.change_x = -self.MOVEMENT_SPEED
        elif self.right_pressed and not self.left_pressed:
            self.change_x = self.MOVEMENT_SPEED


class Enemy(arcade.SpriteSolidColor):
    """Classe que representa o NPC Inimigo e controla sua Inteligência Artificial."""
    def __init__(self):
        super().__init__(30, 30, (255, 100, 100))
        
        # Atributos do Campo de Visão (FOV)
        self.vision_radius = 250
        self.fov = 70
        self.facing_angle = 180
        self.player_detected = False
        
        # Atributos de Inteligência Artificial
        self.patrol_timer = 0
        self.patrol_angle = 180

    def update_ai(self, player_sprite, wall_list, delta_time):
        """Processa as lógicas de visão, detecção e mudança de estado do NPC."""
        dx = player_sprite.center_x - self.center_x
        dy = player_sprite.center_y - self.center_y
        distance = math.hypot(dx, dy)

        self.player_detected = False

        if distance <= self.vision_radius:
            angle_to_player = math.degrees(math.atan2(dy, dx)) #angulo do player em relacao ao inimigo
            angle_diff = (angle_to_player - self.facing_angle + 180) % 360 - 180
            
            #tá dentro do cone
            if abs(angle_diff) <= self.fov / 2:
                # Raycasting
                if arcade.has_line_of_sight(self.position, player_sprite.position, wall_list):
                    self.player_detected = True

        # --- Comportamento da Inteligência Artificial ---
        if self.player_detected:
            self.color = arcade.color.YELLOW
            angle_to_player = math.atan2(dy, dx)
            self.change_x = math.cos(angle_to_player) * 3
            self.change_y = math.sin(angle_to_player) * 3
            self.facing_angle = math.degrees(angle_to_player)
        else:
            self.color = (255, 100, 100)
            self.patrol_timer -= delta_time
            if self.patrol_timer <= 0:
                self.patrol_angle = random.uniform(0, 360)
                self.patrol_timer = random.uniform(1.0, 3.0)
            
            self.change_x = math.cos(math.radians(self.patrol_angle)) * 1.5
            self.change_y = math.sin(math.radians(self.patrol_angle)) * 1.5
            self.facing_angle = self.patrol_angle

    def draw_fov(self):#desenha cone
        start_angle = math.radians(self.facing_angle - self.fov / 2)
        end_angle = math.radians(self.facing_angle + self.fov / 2)
        
        ex, ey = self.center_x, self.center_y
        # pontas do cone
        p1 = (ex, ey)
        p2 = (ex + self.vision_radius * math.cos(start_angle), ey + self.vision_radius * math.sin(start_angle))
        p3 = (ex + self.vision_radius * math.cos(end_angle), ey + self.vision_radius * math.sin(end_angle))
              
        cone_color = (255, 215, 0, 90) if self.player_detected else (255, 255, 255, 70)
        arcade.draw_polygon_filled((p1, p2, p3), cone_color)

class MeuJogo(arcade.Window):
    """
    Classe principal do jogo.
    """

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        
        arcade.set_background_color((15, 15, 15))

        self.player_list = None
        self.enemy_list = None
        self.wall_list = None
        
        self.player_sprite = None
        self.enemy_sprite = None
        
        # Física e Movimentação
        self.physics_engine = None
        self.enemy_physics_engine = None
        self.game_over = False

    def setup(self):
        """
        Configura o jogo e inicializa as variáveis.
        Deve ser chamado para iniciar o jogo ou reiniciar a partida.
        """
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()

        self.player_sprite = Player()
        self.player_sprite.center_x = SCREEN_WIDTH // 4
        self.player_sprite.center_y = SCREEN_HEIGHT // 2
        self.player_list.append(self.player_sprite)
        
        # (largura, altura, centro_x, centro_y)
        paredes_config = [
            
            (800, 20, 400, 590), # Topo
            (800, 20, 400, 10),  # Base
            (20, 600, 10, 300),  # Esquerda
            (20, 600, 790, 300), # Direita
            
            
            (100, 20, 150, 450), 
            (20, 200, 600, 450), 
            (300, 20, 550, 150), 
            (20, 250, 250, 200), 
            (100, 100, 400, 300),
            (20, 150, 400, 100), 
        ]

        for largura, altura, cx, cy in paredes_config:
            parede = arcade.SpriteSolidColor(largura, altura, arcade.color.DARK_GRAY)
            parede.center_x = cx
            parede.center_y = cy
            self.wall_list.append(parede)

        self.enemy_sprite = Enemy()
        self.enemy_sprite.center_x = 650
        self.enemy_sprite.center_y = 350
        self.enemy_list.append(self.enemy_sprite)

        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)
        self.enemy_physics_engine = arcade.PhysicsEngineSimple(self.enemy_sprite, self.wall_list)

        self.game_over = False

    def on_draw(self):
        """
        Renderiza a tela. Chamado automaticamente pelo Arcade.
        """
        self.clear()

        # 1. Desenha o mapa e personagens
        self.player_list.draw()
        self.enemy_list.draw()
        self.wall_list.draw()
        
        # 2. Filtro de Escuridão
        bordas_tela = (
            (0, 0),
            (SCREEN_WIDTH, 0),
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            (0, SCREEN_HEIGHT)
        )
        arcade.draw_polygon_filled(bordas_tela, (0, 0, 0, 180))

        # 3. Desenha o Cone
        if self.enemy_sprite:
            self.enemy_sprite.draw_fov()

        if self.game_over:
            arcade.draw_text("GAME OVER", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20,
                             arcade.color.RED, 54, anchor_x="center", font_name="arial", bold=True)
            arcade.draw_text("Aperte ENTER para recomeçar", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40,
                             arcade.color.WHITE, 24, anchor_x="center", font_name="arial")

    def on_update(self, delta_time):
        """
        Lógica e movimentação do jogo.
        """
        if self.game_over:
            return

        self.player_sprite.update_movement()
        self.enemy_sprite.update_ai(self.player_sprite, self.wall_list, delta_time)

        self.physics_engine.update()
        self.enemy_physics_engine.update()

        # (Game Over)
        if arcade.check_for_collision(self.player_sprite, self.enemy_sprite):
            self.game_over = True

    def on_key_press(self, key, modifiers):
        """Chamado quando uma tecla é pressionada."""
        if self.game_over:
            if key == arcade.key.ENTER or key == arcade.key.RETURN:
                self.setup() 
            return

        if key == arcade.key.UP or key == arcade.key.W:
            self.player_sprite.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.player_sprite.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.right_pressed = True

    def on_key_release(self, key, modifiers):
        """Chamado quando uma tecla é solta."""
        if key == arcade.key.UP or key == arcade.key.W:
            self.player_sprite.up_pressed = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.player_sprite.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.right_pressed = False

def main():
    """Função principal."""
    window = MeuJogo()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
