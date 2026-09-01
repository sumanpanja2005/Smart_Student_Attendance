# ML Workspace & Pipeline Architecture

This directory contains the machine learning and computer vision pipeline for the **AI-Based Smart Attendance & Student Analytics System**.

## Subdirectories

- **`datasets/`**: Face image datasets and feature vectors.
- **`models/`**: Serialized ML model artifacts (e.g. Scikit-learn risk classifiers) and pre-extracted facial feature embeddings.
- **`notebooks/`**: Jupyter notebooks for dataset exploration, face model evaluation, and risk classification model training.
- **`preprocessing/`**: Face image normalization, dataset preparation scripts, and feature engineering utilities.

---

## Future ML/CV Engine Stack
- **OpenCV (`opencv-python`)**: Camera frame acquisition and image preprocessing.
- **InsightFace (`insightface`)**: High-accuracy deep facial embedding extraction and face detection.
- **Scikit-learn (`scikit-learn`)**: Student academic risk prediction (early-warning classifier based on attendance patterns and grades).
- **NumPy (`numpy`)**: Vector arithmetic and similarity metric calculations (Cosine similarity / Euclidean distance).

*Note: AI/ML dependencies will be integrated in subsequent project implementation phases.*
