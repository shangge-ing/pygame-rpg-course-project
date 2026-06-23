from pathlib import Path

import pygame

from .settings import BASE_DIR, SWK2_DIR


def generate_preview(output_path=None, columns=16, cell_size=(92, 116)):
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1, 1))

    paths = sorted(Path(SWK2_DIR).glob("*.png"))
    if not paths:
        raise FileNotFoundError(f"no swk2 frames found in {SWK2_DIR}")

    rows = (len(paths) + columns - 1) // columns
    cell_width, cell_height = cell_size
    label_height = 22
    surface = pygame.Surface((columns * cell_width, rows * cell_height), pygame.SRCALPHA)
    surface.fill((28, 32, 38, 255))
    font = pygame.font.Font(None, 16)

    for index, path in enumerate(paths):
        image = pygame.image.load(path).convert_alpha()
        column = index % columns
        row = index // columns
        cell_x = column * cell_width
        cell_y = row * cell_height

        draw_rect = pygame.Rect(cell_x, cell_y, cell_width, cell_height - label_height)
        pygame.draw.rect(surface, (38, 43, 50), (cell_x + 1, cell_y + 1, cell_width - 2, cell_height - 2))
        scale = min((cell_width - 16) / image.get_width(), (cell_height - label_height - 12) / image.get_height(), 1.35)
        size = (max(1, round(image.get_width() * scale)), max(1, round(image.get_height() * scale)))
        preview = pygame.transform.smoothscale(image, size)
        surface.blit(preview, preview.get_rect(midbottom=(draw_rect.centerx, draw_rect.bottom - 4)))

        label = f"{index + 1:03d}"
        text = font.render(label, True, (235, 235, 235))
        surface.blit(text, text.get_rect(center=(cell_x + cell_width // 2, cell_y + cell_height - 12)))

    output = Path(output_path) if output_path else BASE_DIR / "docs" / "swk2_preview.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, output)
    return output


if __name__ == "__main__":
    print(generate_preview())
