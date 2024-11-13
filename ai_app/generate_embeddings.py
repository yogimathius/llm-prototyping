from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import pickle
import logging


def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Load embedding model
    logger.info("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Load texts
    base_path = Path("datasets")
    all_texts = []
    all_sources = []

    # Load CSVs
    try:
        logger.info("Loading CSV files...")

        # Buddha quotes
        buddha_path = base_path / "buddha_quotes.csv"
        if buddha_path.exists():
            buddha_quotes = pd.read_csv(buddha_path)
            all_texts.extend(
                buddha_quotes["Quote"].tolist()
            )  # Changed from 'quote' to 'Quote'
            all_sources.extend(["Buddha"] * len(buddha_quotes))
            logger.info(f"Loaded {len(buddha_quotes)} Buddha quotes")

        # Asana benefits
        asana_path = base_path / "asana_benefits.csv"
        if asana_path.exists():
            asana_benefits = pd.read_csv(asana_path)
            all_texts.extend(
                asana_benefits["Description"].tolist()
            )  # Changed from 'description' to 'Description'
            all_sources.extend(["Yoga"] * len(asana_benefits))
            logger.info(f"Loaded {len(asana_benefits)} Asana benefits")

        # Meditation
        meditation_path = base_path / "meditation.csv"
        if meditation_path.exists():
            meditation = pd.read_csv(meditation_path)
            # Combine Name and Description for more context
            meditation_texts = [
                f"{row['Name']}: {row['Description']}"
                for _, row in meditation.iterrows()
            ]
            all_texts.extend(meditation_texts)
            all_sources.extend(["Meditation"] * len(meditation))
            logger.info(f"Loaded {len(meditation)} meditation entries")

        # Rumi poetry
        rumi_path = base_path / "rumi_poetry.xlsx"
        if rumi_path.exists():
            rumi_poetry = pd.read_excel(rumi_path)
            all_texts.extend(
                rumi_poetry["Poem"].tolist()
            )  # Changed from 'poem' to 'Poem'
            all_sources.extend(["Rumi"] * len(rumi_poetry))
            logger.info(f"Loaded {len(rumi_poetry)} Rumi poems")

        logger.info(f"Total texts loaded: {len(all_texts)}")

        # Create embeddings
        logger.info(f"Creating embeddings for {len(all_texts)} texts...")
        embeddings = model.encode(all_texts, show_progress_bar=True)

        # Create knowledge base
        knowledge_base = {
            "texts": all_texts,
            "sources": all_sources,
            "embeddings": embeddings,
        }

        # Save embeddings
        cache_path = base_path / "cached_embeddings.pkl"
        logger.info(f"Saving embeddings to {cache_path}")
        with open(cache_path, "wb") as f:
            pickle.dump(knowledge_base, f)

        logger.info("Done! Embeddings saved successfully.")

        # Optional: Test the embeddings
        test_query = "What is the meaning of life?"
        query_embedding = model.encode(test_query)
        similarities = np.dot(embeddings, query_embedding)
        top_indices = np.argsort(similarities)[-3:][::-1]

        print("\nTesting embeddings with query:", test_query)
        for idx in top_indices:
            print(f"\nFrom {all_sources[idx]}:")
            print(all_texts[idx])
            print(f"Similarity score: {similarities[idx]:.4f}")

    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        raise

    # Comment out the rest of the code for now until we fix the column names


if __name__ == "__main__":
    main()
