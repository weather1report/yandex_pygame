import sys
import os
import pygame
import random

GRAVITY = 9.8
pygame.init()
pygame.display.set_caption('game')
size = width, height = 800, 600
screen = pygame.display.set_mode(size)

all_sprites = pygame.sprite.Group()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


FPS = 50


def terminate():
    pygame.quit()
    sys.exit()


def start_screen(n):
    intro_text = ['Перемещение - WASD', 'пропуск уровня - SPACE', 'ваша задача спустится по этажам подземелья',
                  'нажмите любую кнопку чтобы продолжить']
    intro_text_end = ['ВЫ ВЫЙГРАЛИ!!!!!', 'нажмите любую кнопку чтобы нчать заново']
    fon = pygame.transform.scale(load_image(('start.jpg' if n == 0 else 'end_screen.jpg')), (800, 600))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 30)
    text_coord = (20 if n == 0 else 20)
    for line in (intro_text if n == 0 else intro_text_end):
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return  # начинаем игру
        pygame.display.flip()
        clock.tick(FPS)


def load_level(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '-'), level_map))


tile_width = tile_height = 50
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
tile_crash = pygame.sprite.Group()


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        if tile_type in ('wall', 'box'):
            super().__init__(tiles_group, all_sprites, tile_crash)
        else:
            super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        sheet = load_image("hero12.png", -1)
        columns, rows = 12, 1
        super().__init__(player_group, all_sprites)

        self.framemod = 0
        self.fps = 5
        self.fpscounter = 0
        self.moveconter = 0
        self.healf = 2
        self.death = 0
        self.damage_deal = 0
        self.demageimage = load_image('None.png', -1)

        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x - 10, tile_height * pos_y - 5)
        self.pos_x, self.pos_y = pos_x, pos_y

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.fpscounter += 1
        self.moveconter += 1
        if maap[self.pos_y][self.pos_x] in ('lava') and self.death != -1:
            self.damage()
        if self.fpscounter > 30 / self.fps:
            self.fpscounter = 0
            self.cur_frame = (self.cur_frame + 1) % 3 + self.framemod * 3
            self.image = self.frames[self.cur_frame]
            if self.death == -1:
                self.damage_deal += 1
                if self.damage_deal % 3 == 1:
                    self.image = self.demageimage
                if self.damage_deal > 30 / self.fps:
                    self.death = 0

    def move(self, event):
        global maap
        if self.moveconter < (5 if self.death >= 0 else 20):
            return
        if event.key == pygame.K_w:
            self.framemod = 1
            if maap[self.pos_y - 1][self.pos_x] not in ('box', 'wall', 'bow'):
                self.pos_y -= 1
                self.rect[1] -= tile_height
                self.moveconter = 0
        elif event.key == pygame.K_s:
            self.framemod = 0
            if maap[self.pos_y + 1][self.pos_x] not in ('box', 'wall', 'bow'):
                self.pos_y += 1
                self.rect[1] += tile_height
                self.moveconter = 0
        elif event.key == pygame.K_a:
            self.framemod = 2
            if maap[self.pos_y][self.pos_x - 1] not in ('box', 'wall', 'bow'):
                self.pos_x -= 1
                self.rect[0] -= tile_width
                self.moveconter = 0
        elif event.key == pygame.K_d:
            self.framemod = 3
            if maap[self.pos_y][self.pos_x + 1] not in ('box', 'wall', 'bow'):
                self.pos_x += 1
                self.rect[0] += tile_width
                self.moveconter = 0

    def damage(self):
        global level_status
        if self.death >= 0:
            self.healf -= 1
            create_particles((self.rect[0] + 28, self.rect[1] + 2))
            if self.healf > 0:
                self.death = -1
                self.damage_deal = 0
            else:
                self.death = 1
                level_status = -1


particle_group = pygame.sprite.Group()


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image("star.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))
    fire = fire[1:]

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites, particle_group)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = GRAVITY
        self.fpsconter = 0

    def update(self):
        self.fpsconter += 1
        if self.fpsconter > 4:
            self.fpsconter = 0
            # применяем гравитационный эффект:
            # движение с ускорением под действием гравитации
            self.velocity[1] += self.gravity
            # перемещаем частицу
            self.rect.x += self.velocity[0]
            self.rect.y += self.velocity[1]
            # убиваем, если частица ушла за экран
            if not self.rect.colliderect(player.rect[0] - 100, player.rect[1] - 100, 200, 200):
                self.kill()


class Bow(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(tiles_group, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)

        self.napr = tile_type[4:]
        if tile_type[2] == 'w':
            self.fpsconter = 0
        else:
            self.fpsconter = 30

    def update(self):
        self.fpsconter += 1
        if self.fpsconter > 60:
            self.fpsconter = 0
            Arrow(self.napr, self.rect.x, self.rect.y)


arrows_group = pygame.sprite.Group()


class Arrow(pygame.sprite.Sprite):
    def __init__(self, napr, pos_x, pos_y):
        super().__init__(all_sprites, arrows_group)
        self.image = pygame.transform.scale(load_image(str('arrow_' + napr + '.png'), -1), (30, 30))
        self.rect = self.image.get_rect().move(pos_x, pos_y)
        if napr == 'right':
            self.rect.y += 6
        elif napr == 'down':
            self.rect.x += 10
        elif napr == 'left':
            self.rect.y += 5
        else:
            self.rect.x += 10
        self.napr = napr
        self.fpsconter = 4

    def update(self):
        if self.napr == 'right':
            self.rect.x += self.fpsconter
        elif self.napr == 'down':
            self.rect.y += self.fpsconter
        elif self.napr == 'left':
            self.rect.x -= self.fpsconter
        else:
            self.rect.y -= self.fpsconter

        if pygame.sprite.spritecollideany(self, player_group):
            player.damage()
            self.kill()
        if pygame.sprite.spritecollideany(self, tile_crash):
            self.kill()


spikes_group = pygame.sprite.Group()


class Spike(pygame.sprite.Sprite):
    def __init__(self, hoe, pos_x, pos_y):
        super().__init__(all_sprites, spikes_group)
        self.sheet = (pygame.transform.scale(load_image('spike_n.png', -1), (50, 50)),
                      pygame.transform.scale(load_image('spike.png', -1), (50, 50)))
        self.life = (0 if hoe == 'spike' else 1)
        self.image = self.sheet[self.life]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.fpsconter = (20 if hoe == 'spike' else 0)
        self.posx, self.posy = pos_x, pos_y

    def update(self):
        self.fpsconter += 1
        if (self.fpsconter >= 60 and self.life == 0) or (self.fpsconter >= 20 and self.life == 1):
            self.fpsconter = 0
            self.life = (self.life + 1) % 2
            self.image = self.sheet[self.life]

        if self.life == 1 and self.posx == player.pos_x and self.posy == player.pos_y:
            player.damage()


end_group = pygame.sprite.Group()


class Endlevel(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, end_group)
        self.image = pygame.transform.scale(load_image('end.png'), (50, 50))
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.posx, self.posy = pos_x, pos_y
        self.fpsconter = 0
        self.check = 0

    def update(self):
        global level_status
        if self.posx == player.pos_x and self.posy == player.pos_y:
            level_status = 1


def create_particles(position):
    # количество создаваемых частиц
    particle_count = 5
    # возможные скорости
    numbers = range(-20, 20)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


player = None
maap = []
# 1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111
tile_images = {
    'wall': pygame.transform.scale(load_image('rock.jpg', -1), (50, 50)),
    'empty': pygame.transform.scale(load_image('grass3.jpg', -1), (60, 60)),
    'box': pygame.transform.scale(load_image('box.png', -1), (50, 50)),
    'lava': pygame.transform.scale(load_image('lava.jpg', -1), (50, 50)),
    'bow_right': pygame.transform.scale(load_image('bow_right.png'), (50, 50)),
    'bow_down': pygame.transform.scale(load_image('bow_down.png'), (50, 50)),
    'bow_left': pygame.transform.scale(load_image('bow_left.png'), (50, 50)),
    'bow_up': pygame.transform.scale(load_image('bow_up.png'), (50, 50)),
    'boW_right': pygame.transform.scale(load_image('bow_right.png'), (50, 50)),
    'boW_down': pygame.transform.scale(load_image('bow_down.png'), (50, 50)),
    'boW_left': pygame.transform.scale(load_image('bow_left.png'), (50, 50)),
    'boW_up': pygame.transform.scale(load_image('bow_up.png'), (50, 50)),
    'spike': pygame.transform.scale(load_image('spike.png', -1), (50, 50)),
    'spike2': pygame.transform.scale(load_image('spike.png', -1), (50, 50)),
    'none': pygame.transform.scale(load_image('None2.png'), (50, 50))
}
tile_shifr = {
    '.': 'empty',
    '#': 'wall',
    '@': 'empty',
    '?': 'box',
    'l': 'lava',
    '1': 'bow_right',
    '2': 'bow_down',
    '3': 'bow_left',
    '4': 'boW_up',
    '5': 'boW_right',
    '6': 'boW_down',
    '7': 'boW_left',
    '8': 'boW_up',
    '>': 'spike',
    '<': 'spike2',
    '+': 'end',
    '-': 'none'
}


def generate_level(level):
    global maap
    new_player, x, y = None, None, None
    for y in range(len(level)):
        maap.append([])
        for x in range(len(level[y])):
            if tile_shifr[level[y][x]][:3] in ('bow', 'boW'):
                Bow(tile_shifr[level[y][x]], x, y)
                maap[-1].append('bow')
            elif tile_shifr[level[y][x]] in ('spike', 'spike2'):
                Tile('empty', x, y)
                Spike(tile_shifr[level[y][x]], x, y)
                maap[-1].append('empty')
            elif tile_shifr[level[y][x]] == 'end':
                Endlevel(x, y)
                maap[-1].append('empty')
            else:
                Tile(tile_shifr[level[y][x]], x, y)
                maap[-1].append(tile_shifr[level[y][x]])
            if level[y][x] == '@':
                new_player = Player(x, y)
    return new_player, x, y


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dy = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.y += self.dy

    # позиционировать камеру на объекте target
    def update(self, target):
        self.dy = -(target.rect.y + target.rect.h // 2 - height // 2)


camera = Camera()

if __name__ == '__main__':
    running = True
    clock = pygame.time.Clock()
    while running:
        start_screen(0)

        # level 111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111
        maap = []
        level = []
        player, level_x, level_y = generate_level(load_level('map.txt'))
        size = width, height = 800, 600
        screen2 = pygame.display.set_mode(size)
        level_status = 0
        while running and level_status == 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    player.move(event)
                    if event.key == pygame.K_SPACE:
                        level_status = 1
                        break

            camera.update(player)
            # обновляем положение всех спрайтов
            for sprite in all_sprites:
                camera.apply(sprite)
            all_sprites.update()
            tiles_group.draw(screen2)
            end_group.draw(screen2)
            spikes_group.draw(screen2)
            arrows_group.draw(screen2)
            player_group.draw(screen2)
            particle_group.draw(screen2)
            pygame.display.flip()
            clock.tick(30)

        for i in all_sprites:
            i.kill()
        if level_status == -1:
            continue
        level_status = 0

        # level 222222222222222222222222222222222222222222222222222222222222222222222222222222222222222222

        maap = []
        level = []
        player, level_x, level_y = generate_level(load_level('map2.txt'))
        size = width, height = 800, 600
        screen2 = pygame.display.set_mode(size)
        while running and level_status == 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    player.move(event)
                    if event.key == pygame.K_SPACE:
                        level_status = 1
                        break

            camera.update(player)
            for sprite in all_sprites:
                camera.apply(sprite)
            all_sprites.update()
            tiles_group.draw(screen2)
            end_group.draw(screen2)
            spikes_group.draw(screen2)
            arrows_group.draw(screen2)
            player_group.draw(screen2)
            particle_group.draw(screen2)
            pygame.display.flip()
            clock.tick(30)

        for i in all_sprites:
            i.kill()
        if level_status == -1:
            continue

        # last_screen
        if level_status != 0:
            start_screen(1)

        level_status = 0
