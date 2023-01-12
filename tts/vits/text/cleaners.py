""" from https://github.com/keithito/tacotron """

'''
Cleaners are transformations that run over the input text at both training and eval time.

Cleaners can be selected by passing a comma-delimited list of cleaner names as the "cleaners"
hyperparameter. Some cleaners are English-specific. You'll typically want to use:
  1. "english_cleaners" for English text
  2. "transliteration_cleaners" for non-English text that can be transliterated to ASCII using
     the Unidecode library (https://pypi.python.org/pypi/Unidecode)
  3. "basic_cleaners" if you do not want to transliterate (in this case, you should also update
     the symbols in symbols.py to match your data).
'''

import re
from unidecode import unidecode
from phonemizer import phonemize
# from numbers import normalize_numbers
from jamo import h2j, j2hcj
import jamo
from ko_pron import romanise


# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')

# List of (regular expression, replacement) pairs for abbreviations:
_abbreviations = [(re.compile('\\b%s\\.' % x[0], re.IGNORECASE), x[1]) for x in [
  ('mrs', 'misess'),
  ('mr', 'mister'),
  ('dr', 'doctor'),
  ('st', 'saint'),
  ('co', 'company'),
  ('jr', 'junior'),
  ('maj', 'major'),
  ('gen', 'general'),
  ('drs', 'doctors'),
  ('rev', 'reverend'),
  ('lt', 'lieutenant'),
  ('hon', 'honorable'),
  ('sgt', 'sergeant'),
  ('capt', 'captain'),
  ('esq', 'esquire'),
  ('ltd', 'limited'),
  ('col', 'colonel'),
  ('ft', 'fort'),
]]

_korean_classifiers = '군데 권 개 그루 닢 대 두 마리 모 모금 뭇 발 발짝 방 번 벌 보루 살 수 술 시 쌈 움큼 정 짝 채 척 첩 축 켤레 톨 통'

_hangul_divided = [(re.compile('%s' % x[0]), x[1]) for x in [
  ('ㄳ', 'ㄱㅅ'),
  ('ㄵ', 'ㄴㅈ'),
  ('ㄶ', 'ㄴㅎ'),
  ('ㄺ', 'ㄹㄱ'),
  ('ㄻ', 'ㄹㅁ'),
  ('ㄼ', 'ㄹㅂ'),
  ('ㄽ', 'ㄹㅅ'),
  ('ㄾ', 'ㄹㅌ'),
  ('ㄿ', 'ㄹㅍ'),
  ('ㅀ', 'ㄹㅎ'),
  ('ㅄ', 'ㅂㅅ'),
  ('ㅘ', 'ㅗㅏ'),
  ('ㅙ', 'ㅗㅐ'),
  ('ㅚ', 'ㅗㅣ'),
  ('ㅝ', 'ㅜㅓ'),
  ('ㅞ', 'ㅜㅔ'),
  ('ㅟ', 'ㅜㅣ'),
  ('ㅢ', 'ㅡㅣ'),
  ('ㅑ', 'ㅣㅏ'),
  ('ㅒ', 'ㅣㅐ'),
  ('ㅕ', 'ㅣㅓ'),
  ('ㅖ', 'ㅣㅔ'),
  ('ㅛ', 'ㅣㅗ'),
  ('ㅠ', 'ㅣㅜ')
]]

_latin_to_hangul = [(re.compile('%s' % x[0], re.IGNORECASE), x[1]) for x in [
  ('a', '에이'),
  ('b', '비'),
  ('c', '시'),
  ('d', '디'),
  ('e', '이'),
  ('f', '에프'),
  ('g', '지'),
  ('h', '에이치'),
  ('i', '아이'),
  ('j', '제이'),
  ('k', '케이'),
  ('l', '엘'),
  ('m', '엠'),
  ('n', '엔'),
  ('o', '오'),
  ('p', '피'),
  ('q', '큐'),
  ('r', '아르'),
  ('s', '에스'),
  ('t', '티'),
  ('u', '유'),
  ('v', '브이'),
  ('w', '더블유'),
  ('x', '엑스'),
  ('y', '와이'),
  ('z', '제트')
]]

def expand_abbreviations(text):
  for regex, replacement in _abbreviations:
    text = re.sub(regex, replacement, text)
  return text

'''
def expand_numbers(text):
  return normalize_numbers(text)
'''

def lowercase(text):
  return text.lower()


def collapse_whitespace(text):
  return re.sub(_whitespace_re, ' ', text)


def replace_without_hangul(text):
  return re.sub(re.compile(r'[!?.,;:~]+'), '', text)


def convert_to_ascii(text):
  return unidecode(text)


def latin_to_hangul(text):
  for regex, replacement in _latin_to_hangul:
    text = re.sub(regex, replacement, text)
  return text


def divide_hangul(text):
  for regex, replacement in _hangul_divided:
    text = re.sub(regex, replacement, text)
  return text


def hangul_number(num, sino=True):
  '''Reference https://github.com/Kyubyong/g2pK'''
  num = re.sub(',', '', num)

  if num == '0':
      return '영'
  if not sino and num == '20':
      return '스무'

  digits = '123456789'
  names = '일이삼사오육칠팔구'
  digit2name = {d: n for d, n in zip(digits, names)}

  modifiers = '한 두 세 네 다섯 여섯 일곱 여덟 아홉'
  decimals = '열 스물 서른 마흔 쉰 예순 일흔 여든 아흔'
  digit2mod = {d: mod for d, mod in zip(digits, modifiers.split())}
  digit2dec = {d: dec for d, dec in zip(digits, decimals.split())}

  spelledout = []
  for i, digit in enumerate(num):
    i = len(num) - i - 1
    if sino:
      if i == 0:
        name = digit2name.get(digit, '')
      elif i == 1:
        name = digit2name.get(digit, '') + '십'
        name = name.replace('일십', '십')
    else:
      if i == 0:
        name = digit2mod.get(digit, '')
      elif i == 1:
        name = digit2dec.get(digit, '')
    if digit == '0':
      if i % 4 == 0:
        last_three = spelledout[-min(3, len(spelledout)):]
        if ''.join(last_three) == '':
          spelledout.append('')
          continue
      else:
        spelledout.append('')
        continue
    if i == 2:
      name = digit2name.get(digit, '') + '백'
      name = name.replace('일백', '백')
    elif i == 3:
      name = digit2name.get(digit, '') + '천'
      name = name.replace('일천', '천')
    elif i == 4:
      name = digit2name.get(digit, '') + '만'
      name = name.replace('일만', '만')
    elif i == 5:
      name = digit2name.get(digit, '') + '십'
      name = name.replace('일십', '십')
    elif i == 6:
      name = digit2name.get(digit, '') + '백'
      name = name.replace('일백', '백')
    elif i == 7:
      name = digit2name.get(digit, '') + '천'
      name = name.replace('일천', '천')
    elif i == 8:
      name = digit2name.get(digit, '') + '억'
    elif i == 9:
      name = digit2name.get(digit, '') + '십'
    elif i == 10:
      name = digit2name.get(digit, '') + '백'
    elif i == 11:
      name = digit2name.get(digit, '') + '천'
    elif i == 12:
      name = digit2name.get(digit, '') + '조'
    elif i == 13:
      name = digit2name.get(digit, '') + '십'
    elif i == 14:
      name = digit2name.get(digit, '') + '백'
    elif i == 15:
      name = digit2name.get(digit, '') + '천'
    spelledout.append(name)
  return ''.join(elem for elem in spelledout)


def number_to_hangul(text):
  '''Reference https://github.com/Kyubyong/g2pK'''
  tokens = set(re.findall(r'(\d[\d,]*)([\uac00-\ud71f]+)', text))
  for token in tokens:
    num, classifier = token
    if classifier[:2] in _korean_classifiers or classifier[0] in _korean_classifiers:
      spelledout = hangul_number(num, sino=False)
    else:
      spelledout = hangul_number(num, sino=True)
    text = text.replace(f'{num}{classifier}', f'{spelledout}{classifier}')
  # digit by digit for remaining digits
  digits = '0123456789'
  names = '영일이삼사오육칠팔구'
  for d, n in zip(digits, names):
    text = text.replace(d, n)
  return text


def basic_cleaners(text):
  '''Basic pipeline that lowercases and collapses whitespace without transliteration.'''
  text = lowercase(text)
  text = collapse_whitespace(text)
  return text


def transliteration_cleaners(text):
  '''Pipeline for non-English text that transliterates to ASCII.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = collapse_whitespace(text)
  return text


def english_cleaners(text):
  '''Pipeline for English text, including abbreviation expansion.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = expand_abbreviations(text)
  phonemes = phonemize(text, language='en-us', backend='espeak', strip=True)
  phonemes = collapse_whitespace(phonemes)
  return phonemes


def english_cleaners2(text):
  '''Pipeline for English text, including abbreviation expansion. + punctuation + stress'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = expand_abbreviations(text)
  phonemes = phonemize(text, language='en-us', backend='espeak', strip=True, preserve_punctuation=True, with_stress=True)
  phonemes = collapse_whitespace(phonemes)
  return phonemes

def korean_cleaners(text):
  text = latin_to_hangul(text)
  text = number_to_hangul(text)
  text = replace_without_hangul(text)
  text = collapse_whitespace(text)
  phonemes = romanise(text.strip(), "ipa")
  if '~' in phonemes:
    phonemes = phonemes[:phonemes.index(']')]
  phonemes = collapse_whitespace(phonemes)
  return phonemes

def korean_cleaners2(text):
  text = latin_to_hangul(text)
  text = number_to_hangul(text)
  text = j2hcj(h2j(text))
  text = divide_hangul(text)
  return text