"""
NLP Classifier for email categorization using scikit-learn.
"""
import os
import pickle
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


class EmailClassifier:
    """Local NLP classifier for categorizing emails into predefined categories."""
    
    CATEGORIES = ["Work", "Personal", "Spam", "Promotions"]
    
    def __init__(self, model_path: str = "./models/classifier.pkl"):
        """
        Initialize the EmailClassifier.
        
        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = model_path
        
        # Create TfidfVectorizer with specified parameters
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # Create MultinomialNB classifier with specified alpha
        classifier = MultinomialNB(alpha=0.1)
        
        # Build sklearn Pipeline combining vectorizer and classifier
        self.pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', classifier)
        ])
        
        self._is_trained = False
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            self.load_model()
    
    def train(self, training_data: List[Tuple[str, str]]):
        """
        Train the classifier on labeled data.
        
        Args:
            training_data: List of tuples (text, category)
        """
        if not training_data:
            raise ValueError("Training data cannot be empty")
        
        # Separate texts and labels
        texts = [text for text, _ in training_data]
        labels = [label for _, label in training_data]
        
        # Validate categories
        for label in labels:
            if label not in self.CATEGORIES:
                raise ValueError(f"Invalid category: {label}. Must be one of {self.CATEGORIES}")
        
        # Train the pipeline
        self.pipeline.fit(texts, labels)
        self._is_trained = True
    
    def save_model(self):
        """Persist the trained model to disk."""
        if not self._is_trained:
            raise RuntimeError("Cannot save untrained model")
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        # Save the pipeline using pickle
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.pipeline, f)
    
    def load_model(self):
        """
        Load a trained model from disk.
        If model file doesn't exist, train a new model with default training data.
        """
        if not os.path.exists(self.model_path):
            # Handle missing model file by training new model
            try:
                from training_data import get_training_data
                print(f"Model file not found at {self.model_path}. Training new model...")
                training_data = get_training_data()
                self.train(training_data)
                self.save_model()
                print(f"New model trained and saved to {self.model_path}")
                return
            except ImportError:
                raise FileNotFoundError(
                    f"Model file not found: {self.model_path} and training_data.py not available"
                )
        
        # Load the pipeline using pickle
        with open(self.model_path, 'rb') as f:
            self.pipeline = pickle.load(f)
        
        self._is_trained = True
    
    def classify(self, subject: str, body: str) -> str:
        """
        Classify an email and return its category.
        
        Args:
            subject: Email subject line
            body: Email body text
            
        Returns:
            One of the four categories: Work, Personal, Spam, or Promotions
        """
        if not self._is_trained:
            raise RuntimeError("Model must be trained before classification")
        
        try:
            # Combine subject and body for classification
            combined_text = f"{subject} {body}"
            
            # Use trained pipeline to predict category
            category = self.pipeline.predict([combined_text])[0]
            
            return category
        except Exception as e:
            # Handle classification errors gracefully
            raise RuntimeError(f"Classification failed: {str(e)}")
    
    @property
    def is_trained(self) -> bool:
        """Check if the model is trained."""
        return self._is_trained


if __name__ == "__main__":
    """Command-line interface for training the classifier."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train the email classifier")
    parser.add_argument("--train", action="store_true", help="Train the classifier")
    args = parser.parse_args()
    
    if args.train:
        # Import training data
        try:
            from training_data import get_training_data
            
            classifier = EmailClassifier()
            training_data = get_training_data()
            
            print(f"Training classifier with {len(training_data)} examples...")
            classifier.train(training_data)
            classifier.save_model()
            print(f"Model trained and saved to {classifier.model_path}")
        except ImportError:
            print("Error: training_data.py not found. Please create it first.")
        except Exception as e:
            print(f"Error during training: {e}")
