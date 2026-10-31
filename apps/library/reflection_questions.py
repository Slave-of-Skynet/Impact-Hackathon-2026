"""Owner's Romanian source, version 1. Never edit a published pool in place."""

POOL_VERSION = 1
SOURCE_FRAGMENTS = (
    "Care este momentul tău preferat din carte?",
    "Descrie-l în spațiul recomandat.",
    "Formulează ideea principală a cărții.",
    "Care personaj te-a impresionat cel mai mult? Argumentează de ce.",
    "Dacă ai putea petrece o zi alături de un personaj, pe cine ai alege? Descrie cum ar arăta acea zi.",
    "Ce gând sau citat din carte ai vrea să păstrezi? Scrie-l.",
    "Cui ai recomanda această carte și de ce?",
    "Alege și scrie trei cuvinte care descriu cel mai bine cartea.",
    "Scrie un scurt rezumat al cărții.",
    "Descrie cartea folosind doar cinci cuvinte.",
    "Scrie un mesaj personajului preferat din carte. Poți să-i adresezi o întrebare, să-i oferi un sfat sau să-i spui ce impresie ți-a lăsat.",
    "Scrie ce idee, lecție sau învățătură iei cu tine după această lectură.",
    "Transformă cel mai important eveniment din carte într-o știre. Inventează un titlu și redactează știrea ca un adevărat jurnalist!",
    "Ai la dispoziție cinci propoziții pentru a convinge un alt cititor să citească această carte.",
    "Completează propoziția: „După ce am citit această carte, am înțeles că...”",
    "Ce mesaj ai transmite tuturor celor care ar citi această carte?",
)

# Working MVP interpretation: source 1+2 is one self-contained question, not an
# owner-confirmed clarification. Stable IDs otherwise retain source numbering.
QUESTION_BANK = {1: " ".join(SOURCE_FRAGMENTS[:2]),
                 **{index: text for index, text in enumerate(SOURCE_FRAGMENTS[2:], start=3)}}
QUESTION_POOLS = {POOL_VERSION: QUESTION_BANK}
