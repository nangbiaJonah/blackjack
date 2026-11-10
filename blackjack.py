
import os
import random
import sys

import pygame

#  settings
W, H = 1200, 675         # table size
FPS = 60
CARD_W, CARD_H = 80, 113   # screen size 
CARD_OFFSET = 34         
BET = 50
START_CHIPS = 500
DECK_POS = (W - 130, 70)

SUITS = ["spades", "hearts", "diamonds", "clubs"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

GREEN = (24, 110, 60)
DARK_GREEN = (14, 78, 42)
WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
RED = (200, 30, 40)
GOLD = (240, 200, 70)
BLUE = (35, 60, 140)
GREY = (90, 90, 90)


#  cards
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.face_up = True
        self.born = 0  

    @property
    def value(self):
        if self.rank == "A":
            return 11
        if self.rank in ("J", "Q", "K"):
            return 10
        return int(self.rank)

    @property
    def color(self):
        return RED if self.suit in ("hearts", "diamonds") else BLACK


def hand_value(cards):
    total = sum(c.value for c in cards)
    aces = sum(1 for c in cards if c.rank == "A")
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


def new_shuffled_deck():
    deck = [Card(r, s) for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck


#  drawing
def draw_suit(surf, suit, cx, cy, r, color):
    if suit == "diamonds":
        pygame.draw.polygon(surf, color, [(cx, cy - r), (cx + r * 0.75, cy),
                                          (cx, cy + r), (cx - r * 0.75, cy)])
    elif suit == "hearts":
        pygame.draw.circle(surf, color, (cx - r * 0.47, cy - r * 0.3), r * 0.55)
        pygame.draw.circle(surf, color, (cx + r * 0.47, cy - r * 0.3), r * 0.55)
        pygame.draw.polygon(surf, color, [(cx - r * 0.98, cy - r * 0.05),
                                          (cx + r * 0.98, cy - r * 0.05),
                                          (cx, cy + r)])
    elif suit == "spades":
        pygame.draw.circle(surf, color, (cx - r * 0.47, cy + r * 0.2), r * 0.55)
        pygame.draw.circle(surf, color, (cx + r * 0.47, cy + r * 0.2), r * 0.55)
        pygame.draw.polygon(surf, color, [(cx - r * 0.98, cy + r * 0.1),
                                          (cx + r * 0.98, cy + r * 0.1),
                                          (cx, cy - r)])
        pygame.draw.polygon(surf, color, [(cx, cy + r * 0.2),
                                          (cx - r * 0.3, cy + r),
                                          (cx + r * 0.3, cy + r)])
    elif suit == "clubs":
        pygame.draw.circle(surf, color, (cx, cy - r * 0.45), r * 0.5)
        pygame.draw.circle(surf, color, (cx - r * 0.5, cy + r * 0.2), r * 0.5)
        pygame.draw.circle(surf, color, (cx + r * 0.5, cy + r * 0.2), r * 0.5)
        pygame.draw.polygon(surf, color, [(cx, cy + r * 0.1),
                                          (cx - r * 0.3, cy + r),
                                          (cx + r * 0.3, cy + r)])


CARD_IMAGES = {}
BACK_IMAGE = None
BG_IMAGE = None
FACES = {}                 # player name 
FACE_DIAMETER = 100        # profile pictures size


def make_circle_avatar(img, d, crisp=False):
    """Crop a picture to a centred square, cut it into a circle of diameter d
    (smooth edges) and add a gold ring around it."""
    w, h = img.get_size()
    k = max(d / w, d / h)                          
    size = (max(d, round(w * k)), max(d, round(h * k)))
    scaler = pygame.transform.scale if crisp else pygame.transform.smoothscale
    img = scaler(img, size)
    square = pygame.Surface((d, d), pygame.SRCALPHA)
    square.blit(img, ((d - size[0]) // 2, (d - size[1]) // 2))

    big = d * 4
    mask = pygame.Surface((big, big), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (big // 2, big // 2), big // 2)
    mask = pygame.transform.smoothscale(mask, (d, d))
    square.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    ring = pygame.Surface((big, big), pygame.SRCALPHA)
    pygame.draw.circle(ring, GOLD, (big // 2, big // 2), big // 2, 14)
    square.blit(pygame.transform.smoothscale(ring, (d, d)), (0, 0))
    return square


def load_card_images():
    """Load the card pictures from the 'cards' folder next to this script.
    Files are named like hearts_A.png, spades_10.png, ... plus back.png."""
    global BACK_IMAGE
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cards")
    size = (CARD_W, CARD_H)

    def load(name):
        img = pygame.image.load(os.path.join(folder, name)).convert()
        return pygame.transform.smoothscale(img, size)

    for suit in SUITS:
        for rank in RANKS:
            CARD_IMAGES[(suit, rank)] = load(f"{suit}_{rank}.png")
    BACK_IMAGE = load("back.png")

    # table background 
    global BG_IMAGE
    try:
        bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "assets", "table.jpg")
        BG_IMAGE = pygame.transform.smoothscale(
            pygame.image.load(bg_path).convert(), (W, H))
    except (pygame.error, FileNotFoundError):
        BG_IMAGE = None

    # character of CPU 
    faces_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "assets", "faces")

    def load_face(folder, name):
        try:
            img = pygame.image.load(os.path.join(faces_dir, folder, name))
            img = img.convert_alpha()
        except (pygame.error, FileNotFoundError):
            return None
        return make_circle_avatar(img, FACE_DIAMETER, crisp=name.endswith(".png"))

    FACES["Dealer"] = {s: load_face("darwin", "darwin.jpg")
                       for s in ("idle", "happy", "sad")}   # one picture only
    for who, folder, prefix, ext in (("CPU 1", "neko", "neko", "png"),
                                     ("CPU 2", "micky", "micky", "jpg")):
        FACES[who] = {s: load_face(folder, f"{prefix}_{s}.{ext}")
                      for s in ("idle", "happy", "sad")}


def draw_card(surf, card, x, y, fonts=None):
    img = CARD_IMAGES[(card.suit, card.rank)] if card.face_up else BACK_IMAGE
    surf.blit(img, (int(x), int(y)))


def draw_text(surf, text, font, color, center=None, topleft=None):
    img = font.render(text, True, color)
    r = img.get_rect()
    if center:
        r.center = center
    if topleft:
        r.topleft = topleft
    surf.blit(img, r)
    return r


#  players
class Player:
    def __init__(self, name, pos, human=False, style="basic", is_dealer=False):
        self.name = name
        self.pos = pos            
        self.human = human
        self.style = style
        self.is_dealer = is_dealer
        self.chips = START_CHIPS
        self.reset()

    def reset(self):
        self.hand = []
        self.status = "playing"   
        self.result = ""

    def card_pos(self, i):
        n = len(self.hand)
        total_w = CARD_W + (n - 1) * CARD_OFFSET
        x = self.pos[0] - total_w / 2 + i * CARD_OFFSET
        return x, self.pos[1]

    @property
    def value(self):
        return hand_value(self.hand)


def cpu_wants_hit(p, dealer_up):
    v = p.value
    if p.style == "basic":              
        return v < 17
    if v >= 17:
        return False
    if v <= 11:
        return True
    return dealer_up not in (2, 3, 4, 5, 6)


#  game
class Game:
    def __init__(self):
        self.dealer = Player("Dealer", (W // 2, 80), is_dealer=True)
        self.you = Player("You", (W // 2, 300), human=True)
        self.cpu1 = Player("CPU 1", (230, 300), style="basic")
        self.cpu2 = Player("CPU 2", (W - 230, 300), style="cautious")
        self.players = [self.you, self.cpu1, self.cpu2]
        self.everyone = [self.dealer] + self.players
        self.deck = []
        self.queue = []
        self.idx = 0
        self.last = 0
        self.message = ""
        self.start_round()

    # round 
    def start_round(self):
        for p in self.everyone:
            p.reset()
            if p.chips < BET:
                p.chips = START_CHIPS
        self.deck = new_shuffled_deck()
        order = self.players + [self.dealer]
        self.queue = [(p, True) for p in order] + \
                     [(p, p is not self.dealer) for p in order]
        self.state = "dealing"
        self.last = pygame.time.get_ticks()
        self.message = "Dealer is dealing..."

    def deal(self, p, face_up=True):
        if not self.deck:
            self.deck = new_shuffled_deck()
        card = self.deck.pop()
        card.face_up = face_up
        card.born = pygame.time.get_ticks()
        p.hand.append(card)

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == "dealing":
            if now - self.last > 330:
                if self.queue:
                    p, up = self.queue.pop(0)
                    self.deal(p, up)
                    self.last = now
                else:
                    for p in self.everyone:
                        if p.value == 21:
                            p.status = "blackjack"
                    if self.dealer.status == "blackjack":
                        self.dealer.hand[1].face_up = True
                        self.finish_round()
                    else:
                        self.idx = 0
                        self.state = "turns"
                        self.last = now

        elif self.state == "turns":
            advanced = False
            while self.idx < len(self.players) and \
                    self.players[self.idx].status != "playing":
                self.idx += 1
                advanced = True
            if advanced:
                self.last = now
            if self.idx >= len(self.players):
                self.state = "dealer"
                self.dealer.hand[1].face_up = True
                self.message = "Dealer reveals the hidden card..."
                self.last = now
                return
            cur = self.players[self.idx]
            if cur.human:
                self.message = "Your turn - [H]it or [S]tand"
            else:
                self.message = f"{cur.name} is thinking..."
                if now - self.last > 900:
                    up = self.dealer.hand[0].value
                    if cpu_wants_hit(cur, up):
                        self.deal(cur)
                        self.check_hand(cur)
                    else:
                        cur.status = "stand"
                    self.last = now

        elif self.state == "dealer":
            if now - self.last > 900:
                live = any(p.status in ("stand", "blackjack") for p in self.players)
                if live and self.dealer.value < 17:
                    self.deal(self.dealer)
                    self.check_hand(self.dealer)
                    self.last = now
                else:
                    if self.dealer.status == "playing":
                        self.dealer.status = "stand"
                    self.finish_round()

    def check_hand(self, p):
        v = p.value
        if v > 21:
            p.status = "bust"
        elif v == 21:
            p.status = "stand"

    def finish_round(self):
        dv = self.dealer.value
        dealer_bj = self.dealer.status == "blackjack"
        for p in self.players:
            pv = p.value
            if p.status == "bust":
                delta = -BET
            elif p.status == "blackjack":
                delta = 0 if dealer_bj else int(BET * 1.5)
            elif dealer_bj:
                delta = -BET
            elif dv > 21 or pv > dv:
                delta = BET
            elif pv == dv:
                delta = 0
            else:
                delta = -BET
            p.chips += delta
            p.result = "PUSH" if delta == 0 else \
                (f"WIN +{delta}" if delta > 0 else f"LOSE {delta}")
        self.state = "result"
        self.message = "Round over - press N / Space to deal again"

    # ---- human input
    def human_turn(self):
        return (self.state == "turns" and self.idx < len(self.players)
                and self.players[self.idx].human
                and self.you.status == "playing")

    def hit(self):
        if self.human_turn():
            self.deal(self.you)
            self.check_hand(self.you)

    def stand(self):
        if self.human_turn():
            self.you.status = "stand"

    # ---- drawing
    def draw(self, surf, fonts, buttons, mouse):
        if BG_IMAGE is not None:
            surf.blit(BG_IMAGE, (0, 0))
        else:
            surf.fill(GREEN)

        now = pygame.time.get_ticks()

        # deck
        for i in range(5):
            draw_card(surf, _BACK, DECK_POS[0] - i * 2, DECK_POS[1] - i * 2, fonts)
        draw_text(surf, f"Deck: {len(self.deck)}", fonts["small"], WHITE,
                  center=(DECK_POS[0] + CARD_W // 2, DECK_POS[1] + CARD_H + 18))

        # players
        for p in self.everyone:
            self.draw_player(surf, p, fonts, now)

        # message bar
        draw_text(surf, self.message, fonts["msg"], GOLD, center=(W // 2, 24))

        # buttons
        for name, rect in buttons.items():
            visible = (name in ("hit", "stand") and self.human_turn()) or \
                      (name == "new" and self.state == "result")
            if not visible:
                continue
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(surf, GOLD if hover else WHITE, rect, border_radius=10)
            pygame.draw.rect(surf, BLACK, rect, 2, border_radius=10)
            label = {"hit": "HIT (H)", "stand": "STAND (S)", "new": "NEW ROUND (N)"}[name]
            draw_text(surf, label, fonts["btn"], BLACK, center=rect.center)

    def draw_player(self, surf, p, fonts, now):
        cx, top = p.pos
        # active-turn 
        active = (self.state == "turns" and self.idx < len(self.players)
                  and self.players[self.idx] is p) or \
                 (self.state == "dealer" and p.is_dealer)
        name_color = GOLD if active else WHITE
        draw_text(surf, p.name, fonts["name"], name_color, center=(cx, top - 28))

        # expression
        faces = FACES.get(p.name)
        if faces:
            if p.is_dealer:
                mood = "idle"
            elif p.status == "bust" or p.result.startswith("LOSE"):
                mood = "sad"
            elif p.result.startswith("WIN"):
                mood = "happy"
            else:
                mood = "idle"
            img = faces.get(mood) or faces.get("idle")
            if img:
                if p.is_dealer:      
                    r = img.get_rect(center=(cx - 170, top + 10))
                else:               
                    r = img.get_rect(midbottom=(cx, top - 48))
                surf.blit(img, r)
        if active:
            pygame.draw.polygon(surf, GOLD, [(cx - 70, top - 36), (cx - 70, top - 20),
                                             (cx - 58, top - 28)])

        for i, card in enumerate(p.hand):
            tx, ty = p.card_pos(i)
            t = min(1.0, (now - card.born) / 250.0)
            t = 1 - (1 - t) ** 3                      
            x = DECK_POS[0] + (tx - DECK_POS[0]) * t
            y = DECK_POS[1] + (ty - DECK_POS[1]) * t
            draw_card(surf, card, x, y, fonts)

        below = top + CARD_H + 22
        if p.is_dealer:
            hidden = any(not c.face_up for c in p.hand)
            if p.hand:
                txt = "?" if hidden else str(p.value)
                draw_text(surf, f"Total: {txt}", fonts["small"], WHITE, center=(cx, below))
        else:
            if p.hand:
                draw_text(surf, f"Total: {p.value}", fonts["small"], WHITE,
                          center=(cx, below))
            draw_text(surf, f"Chips: {p.chips}", fonts["small"], GOLD,
                      center=(cx, below + 22))

        tag = ""
        if p.status == "bust":
            tag = "BUST!"
        elif p.status == "blackjack":
            tag = "BLACKJACK!"
        elif p.status == "stand" and self.state != "result":
            tag = "STAND"
        if tag:
            draw_text(surf, tag, fonts["name"], (255, 120, 120) if tag == "BUST!" else WHITE,
                      center=(cx, below + (22 if p.is_dealer else 46)))
        if p.result:
            col = (120, 255, 140) if p.result.startswith("WIN") else \
                  (255, 120, 120) if p.result.startswith("LOSE") else WHITE
            draw_text(surf, p.result, fonts["name"], col, center=(cx, below + 70))


_BACK = Card("A", "spades")
_BACK.face_up = False


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Blackjack - You vs Dealer with 2 CPU players")
    load_card_images()
    clock = pygame.time.Clock()
    fonts = {
        "title": pygame.font.SysFont("arial", 90, bold=True),
        "name": pygame.font.SysFont("arial", 24, bold=True),
        "msg": pygame.font.SysFont("arial", 28, bold=True),
        "btn": pygame.font.SysFont("arial", 24, bold=True),
        "small": pygame.font.SysFont("arial", 20),
        "card": pygame.font.SysFont("arial", 22, bold=True),
    }
    buttons = {
        "hit": pygame.Rect(W // 2 - 170, H - 125, 150, 50),
        "stand": pygame.Rect(W // 2 + 20, H - 125, 150, 50),
        "new": pygame.Rect(W // 2 - 100, H - 125, 200, 50),
    }
    game = Game()

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if e.key == pygame.K_h:
                    game.hit()
                elif e.key == pygame.K_s:
                    game.stand()
                elif e.key in (pygame.K_n, pygame.K_SPACE, pygame.K_RETURN):
                    if game.state == "result":
                        game.start_round()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if buttons["hit"].collidepoint(e.pos):
                    game.hit()
                elif buttons["stand"].collidepoint(e.pos):
                    game.stand()
                elif buttons["new"].collidepoint(e.pos) and game.state == "result":
                    game.start_round()

        game.update()
        game.draw(screen, fonts, buttons, pygame.mouse.get_pos())
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
