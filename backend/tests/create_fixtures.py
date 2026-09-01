import os
import cv2
import numpy as np


def generate_face_image(
    filename: str,
    skin_color=(190, 220, 245),  # BGR skin tone
    eye_color=(50, 50, 50),
    hair_color=(30, 30, 30),
    shirt_color=(200, 100, 50),
    face_width=130,
    face_height=170,
):
    """Generates a 640x640 portrait test image with realistic skin tone, eyes, nose, lips, hair, and torso."""
    img = np.ones((640, 640, 3), dtype=np.uint8) * 235  # Light background

    # Torso / Shoulders
    cv2.ellipse(img, (320, 600), (220, 140), 0, 0, 180, shirt_color, -1)

    # Neck
    cv2.rectangle(
        img,
        (270, 380),
        (370, 480),
        (
            int(skin_color[0] * 0.9),
            int(skin_color[1] * 0.9),
            int(skin_color[2] * 0.9),
        ),
        -1,
    )

    # Face Oval (Skin tone)
    cv2.ellipse(img, (320, 280), (face_width, face_height), 0, 0, 360, skin_color, -1)

    # Hair
    cv2.ellipse(
        img, (320, 160), (face_width + 10, 85), 0, 180, 360, hair_color, -1
    )

    # Eyebrows
    cv2.line(img, (240, 220), (290, 225), hair_color, 5)
    cv2.line(img, (350, 225), (400, 220), hair_color, 5)

    # Eyes
    cv2.circle(img, (265, 245), 18, (255, 255, 255), -1)
    cv2.circle(img, (375, 245), 18, (255, 255, 255), -1)
    cv2.circle(img, (265, 245), 8, eye_color, -1)
    cv2.circle(img, (375, 245), 8, eye_color, -1)

    # Nose
    cv2.line(img, (320, 250), (315, 290), (140, 170, 200), 3)
    cv2.line(img, (315, 290), (330, 290), (140, 170, 200), 3)

    # Mouth / Lips
    cv2.ellipse(img, (320, 340), (40, 15), 0, 0, 180, (100, 100, 200), -1)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    cv2.imwrite(filename, img)
    print(f"Generated fixture: {filename}")


if __name__ == "__main__":
    fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")

    # Person A
    generate_face_image(
        os.path.join(fixtures_dir, "person_a_1.jpg"),
        skin_color=(190, 220, 245),
        eye_color=(80, 40, 20),
        hair_color=(20, 20, 20),
        shirt_color=(200, 100, 50),
        face_width=130,
        face_height=170,
    )
    generate_face_image(
        os.path.join(fixtures_dir, "person_a_2.jpg"),
        skin_color=(190, 220, 245),
        eye_color=(80, 40, 20),
        hair_color=(20, 20, 20),
        shirt_color=(180, 80, 40),
        face_width=130,
        face_height=170,
    )

    # Person B (Different hair, eye color, shirt)
    generate_face_image(
        os.path.join(fixtures_dir, "person_b_1.jpg"),
        skin_color=(190, 220, 245),
        eye_color=(20, 180, 40),
        hair_color=(200, 180, 50),
        shirt_color=(50, 180, 80),
        face_width=130,
        face_height=170,
    )

    # Multiple faces fixture
    img_multi = np.ones((640, 640, 3), dtype=np.uint8) * 235
    cv2.ellipse(img_multi, (200, 280), (80, 110), 0, 0, 360, (190, 220, 245), -1)
    cv2.circle(img_multi, (170, 250), 10, (255, 255, 255), -1)
    cv2.circle(img_multi, (230, 250), 10, (255, 255, 255), -1)

    cv2.ellipse(img_multi, (440, 280), (80, 110), 0, 0, 360, (190, 220, 245), -1)
    cv2.circle(img_multi, (410, 250), 10, (255, 255, 255), -1)
    cv2.circle(img_multi, (470, 250), 10, (255, 255, 255), -1)

    cv2.imwrite(os.path.join(fixtures_dir, "multiple_faces.jpg"), img_multi)
    print(f"Generated fixture: {os.path.join(fixtures_dir, 'multiple_faces.jpg')}")
