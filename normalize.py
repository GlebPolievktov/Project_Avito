import re
from difflib import SequenceMatcher

class NumberNormalizer:
    

    BASE_NUMBERS = {
        'ноль': 0, 'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
        'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
        'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
        'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18,
        'девятнадцать': 19, 'двадцать': 20, 'тридцать': 30, 'сорок': 40,
        'пятьдесят': 50, 'шестьдесят': 60, 'семьдесят': 70, 'восемьдесят': 80,
        'девяносто': 90, 'сто': 100, 'ста': 100, 'двести': 200, 'триста': 300,
        'четыреста': 400, 'пятьсот': 500, 'шестьсот': 600, 'семьсот': 700,
        'восемьсот': 800, 'девятьсот': 900
    }

    MULTIPLIERS = {
        'тысяча': 1000, 'тысячи': 1000, 'тысяч': 1000, 'тыщу': 1000,
        'миллион': 1000000, 'миллиона': 1000000, 'миллионов': 1000000
    }

    ORDINAL_NUMBERS = {
        'первый': 1, 'второй': 2, 'третий': 3, 'четвертый': 4, 'пятый': 5,
        'шестой': 6, 'седьмой': 7, 'восьмой': 8, 'девятый': 9, 'десятый': 10,
        'двадцатый': 20, 'тридцатый': 30, 'сороковой': 40, 'пятидесятый': 50,
        'сотый': 100, 'тысячный': 1000
    }


    VARIATIONS = {
        'двеси': 'двести', 'петьдесят': 'пятьдесят', 'тыщ': 'тысяч',
        'одинадцать': 'одиннадцать', 'дваста': 'двести'
    }

  
    STOP_WORDS = {'да', 'то', 'есть', 'все', 'вот', 'это', 'как', 'что', 'где'}

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self.lookup_dict = {**self.BASE_NUMBERS, **self.ORDINAL_NUMBERS, **self.MULTIPLIERS}
        self._current_tokens = []

    def _clean_word(self, word: str) -> str:
        #Очистка слова от пунктуации  приведение к нижнему регистру
        return re.sub(r'[^\w]', '', word.lower())

    def _match_number(self, word: str):
        #Нечеткое сопоставление слова со словарем числительных
        if word in self.STOP_WORDS or len(word) < 3:
            return None
        
        if word in self.lookup_dict:
            return word
        
        if word in self.VARIATIONS:
            return self.VARIATIONS[word]

        # длинные слова
        if len(word) > 4:
            best_match = None
            best_ratio = 0
            for candidate in self.lookup_dict.keys():
                ratio = SequenceMatcher(None, word, candidate).ratio()
                if ratio > best_ratio and ratio >= self.threshold:
                    best_ratio = ratio
                    best_match = candidate
            return best_match
        return None

    def _get_groups(self, number_tokens):
        #составные числа 
        if not number_tokens:
            return []

        groups = []
        i = 0
        while i < len(number_tokens):
            pos_i, _, val_i = number_tokens[i]
            current_positions = [pos_i]
            current_total = val_i
            
            j = i + 1
            while j < len(number_tokens):
                pos_j, _, val_j = number_tokens[j]
                
                if pos_j - current_positions[-1] > 2:
                    break
                
                gap_tokens = self._current_tokens[current_positions[-1] + 1 : pos_j]
                if any(sep in gap_tokens for sep in ['и', 'или', 'до', '-', 'по']):
                    break

                is_combined = False
                if val_j in self.MULTIPLIERS.values() and current_total < val_j:
                    current_total *= val_j
                    is_combined = True
                elif val_j < current_total:
                    # Логика сложения (например, 100 + 20 + 5)
                    if (current_total >= 1000 and val_j < 1000) or \
                       (100 <= current_total < 1000 and val_j < 100) or \
                       (10 <= current_total < 100 and val_j < 10):
                        current_total += val_j
                        is_combined = True
                
                if is_combined:
                    current_positions.append(pos_j)
                    j += 1
                else:
                    break
            
            groups.append((current_positions, current_total))
            i = j
        return groups

    def normalize(self, text: str) -> str:

        tokens = text.split()
        self._current_tokens = [self._clean_word(t) for t in tokens]
        
        # 1. Находим все токены, которые похожи на числа
        found_numbers = []
        for i, word in enumerate(self._current_tokens):
            match = self._match_number(word)
            if match:
                found_numbers.append((i, tokens[i], self.lookup_dict[match]))

        if not found_numbers:
            return text

        # 2. Группируем их в составные числа
        groups = self._get_groups(found_numbers)
        
        # 3. Собираем итоговую строку
        result_tokens = tokens.copy()

        for positions, value in sorted(groups, key=lambda x: x[0][0], reverse=True):
            result_tokens[positions[0]] = str(value)
            for extra_pos in sorted(positions[1:], reverse=True):
                del result_tokens[extra_pos]
                
        return ' '.join(result_tokens)
