"""flappy - 终端版 flappy-bird 克隆：重力、拍打、管道、碰撞、--auto 无头演示。"""

import argparse
import random
import sys

WIDTH = 40
HEIGHT = 20
BIRD_X = 8
GRAVITY = 0.45
FLAP_V = -1.4
PIPE_W = 4
PIPE_GAP = 6
PIPE_SPACING = 16
# 相邻管道缺口中心的最大变化量：保证鸟有足够帧数爬升/下落
MAX_GAP_DELTA = 3.5


class Bird:
    def __init__(self, y=None):
        self.y = HEIGHT / 2 if y is None else float(y)
        self.v = 0.0

    def flap(self):
        self.v = FLAP_V

    def step(self):
        self.v += GRAVITY
        self.y += self.v


class Pipe:
    def __init__(self, x, gap_y):
        self.x = x          # 左边缘（浮点）
        self.gap_y = gap_y  # 缺口中心
        self.scored = False

    def collides(self, bird_y):
        bx0, bx1 = BIRD_X - 0.5, BIRD_X + 0.5
        px0, px1 = self.x, self.x + PIPE_W
        if bx1 < px0 or bx0 > px1:
            return False
        top = self.gap_y - PIPE_GAP / 2
        bot = self.gap_y + PIPE_GAP / 2
        return bird_y < top or bird_y > bot


class Game:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.frames = 0
        self.over = False
        self._spawn_timer = PIPE_SPACING
        self._spawn_pipe(initial=True)

    def _spawn_pipe(self, initial=False):
        lo, hi = PIPE_GAP / 2 + 1, HEIGHT - PIPE_GAP / 2 - 1
        if initial or not self.pipes:
            gap_y = self.rng.uniform(lo, hi)
        else:
            prev = self.pipes[-1].gap_y
            gap_y = prev + self.rng.uniform(-MAX_GAP_DELTA, MAX_GAP_DELTA)
            gap_y = max(lo, min(hi, gap_y))
        x = WIDTH if initial else WIDTH + 2
        self.pipes.append(Pipe(x, gap_y))

    def step(self, flap=False):
        if self.over:
            return
        self.frames += 1
        if flap:
            self.bird.flap()
        self.bird.step()
        by = self.bird.y
        if by < 0 or by >= HEIGHT:
            self.over = True
            return
        for p in self.pipes:
            p.x -= 1
            if p.collides(by):
                self.over = True
                return
            if not p.scored and p.x + PIPE_W < BIRD_X:
                p.scored = True
                self.score += 1
        self.pipes = [p for p in self.pipes if p.x + PIPE_W > 0]
        self._spawn_timer -= 1
        if self._spawn_timer <= 0:
            self._spawn_timer = PIPE_SPACING
            self._spawn_pipe()

    def render(self):
        grid = [[" "] * WIDTH for _ in range(HEIGHT)]
        by = int(round(self.bird.y))
        if 0 <= by < HEIGHT:
            grid[by][BIRD_X] = "@"
        for p in self.pipes:
            x0 = int(round(p.x))
            top = int(round(p.gap_y - PIPE_GAP / 2))
            bot = int(round(p.gap_y + PIPE_GAP / 2))
            for x in range(x0, x0 + PIPE_W):
                if 0 <= x < WIDTH:
                    for y in range(0, top):
                        grid[y][x] = "#"
                    for y in range(bot, HEIGHT):
                        grid[y][x] = "#"
        return "\n".join("".join(row) for row in grid)


def auto_play(seed=None, frames=500, verbose=False):
    g = Game(seed)
    for _ in range(frames):
        if g.over:
            break
        # 简单 AI：找最近的管道，鸟低于缺口中心就拍
        target = None
        for p in g.pipes:
            if p.x + PIPE_W >= BIRD_X - 1:
                target = p
                break
        flap = False
        if target is not None and g.bird.v > 0 and g.bird.y > target.gap_y:
            flap = True
        g.step(flap)
        if verbose and g.frames % 50 == 0:
            print(f"帧 {g.frames} 分数 {g.score}")
    return g


def play_interactive(seed=None):
    import time
    g = Game(seed)
    print("flappy: 按回车拍打，q 退出。")
    while not g.over:
        print(f"\n分数 {g.score}\n{g.render()}")
        try:
            line = input("> ")
        except EOFError:
            break
        if line.strip().lower() == "q":
            break
        g.step(flap=True)
    print(f"游戏结束，得分 {g.score}，共 {g.frames} 帧。")


def main(argv=None):
    ap = argparse.ArgumentParser(description="flappy - 终端版 flappy-bird 克隆")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--auto", action="store_true", help="无头自动演示")
    ap.add_argument("--frames", type=int, default=500)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    if args.auto:
        g = auto_play(args.seed, args.frames, args.verbose)
        print(f"自动演示结束：得分 {g.score}，帧数 {g.frames}，"
              f"{'撞毁' if g.over else '存活'}。")
        return 0
    if not sys.stdin.isatty():
        print("交互模式需要终端；请用 --auto。", file=sys.stderr)
        return 2
    play_interactive(args.seed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
