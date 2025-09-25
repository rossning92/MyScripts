from dataclasses import dataclass


@dataclass
class TokenCount:
    input_tokens: int = 0
    output_tokens: int = 0

    def reset(self):
        self.input_tokens = 0
        self.output_tokens = 0


token_count = TokenCount()
