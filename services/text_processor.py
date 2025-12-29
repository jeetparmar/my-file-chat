import re

import tiktoken
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import T5ForConditionalGeneration, T5Tokenizer

from config.settings import (
    DEFAULT_KEYWORDS,
    MAX_KEYWORDS,
    MAX_MODEL_TOKENS,
    MIN_KEYWORDS,
)
from utils.validators import Validators


class TextProcessor:

    @staticmethod
    def clean_text(text: str) -> str:
        return Validators.clean_text(text)

    @staticmethod
    def generate_keywords(text: str, count: int = DEFAULT_KEYWORDS) -> list:
        try:
            count = max(MIN_KEYWORDS, min(count, MAX_KEYWORDS))
            documents = [text]

            vectorizer = TfidfVectorizer(stop_words="english", max_features=count)
            X = vectorizer.fit_transform(documents)
            terms = vectorizer.get_feature_names_out()
            tfidf_scores = X.toarray()[0]

            term_scores = {terms[i]: tfidf_scores[i] for i in range(len(terms))}
            sorted_terms = sorted(term_scores.items(), key=lambda x: x[1], reverse=True)

            return [term for term, _ in sorted_terms[:count]]
        except Exception as e:
            print(f"Error generating keywords: {str(e)}")
            return []

    @staticmethod
    def generate_questions(text: str, count: int = 5) -> list:
        """
        Generate questions from text using T5 model

        Args:
            text: Input text
            count: Number of questions to generate

        Returns:
            List of generated questions
        """
        try:
            model_name = "valhalla/t5-small-qg-prepend"
            tokenizer = T5Tokenizer.from_pretrained(model_name)
            model = T5ForConditionalGeneration.from_pretrained(model_name)

            input_ids = tokenizer.encode(text, return_tensors="pt")
            outputs = model.generate(
                input_ids=input_ids,
                max_length=64,
                num_beams=count,
                num_return_sequences=count,
                early_stopping=True,
            )

            return [
                tokenizer.decode(output, skip_special_tokens=True) for output in outputs
            ]
        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            return []

    @staticmethod
    def format_text(text: str) -> str:
        # Format headers
        formatted_text = re.sub(r"### (.+)", r"### \1", text)
        # Format bold text
        formatted_text = re.sub(r"\*\*(.+?)\*\*", r"**\1**", formatted_text)
        return formatted_text

    @staticmethod
    def count_tokens(text: str, model_name: str = "gpt-3.5-turbo") -> int:
        try:
            encoding = tiktoken.encoding_for_model(model_name)
            return len(encoding.encode(text))
        except Exception as e:
            print(f"Error counting tokens: {str(e)}")
            return 0

    @staticmethod
    def validate_token_limit(
        text: str, max_tokens: int = MAX_MODEL_TOKENS, model_name: str = "gpt-3.5-turbo"
    ) -> bool:
        token_count = TextProcessor.count_tokens(text, model_name)
        return token_count < max_tokens
