'''env
TARGET=3-1-Entwurf-md
'''
import traceback
from entwurf import entwurf


if __name__ == "__main__":

    try:
        text = entwurf()
    except Exception:
        with open('error.log', 'a', encoding='utf-8') as log:
            log.write(traceback.format_exc())
        raise

    file = './Entwurf.md'
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)
