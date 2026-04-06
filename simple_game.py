import random
from collections import Counter

# aliases for suit numbers to make code more readable
# staring at 0 to use and array index if needed
DIAMONDS = 0
CLUBS = 1
HEARTS = 2
SPADES = 3

# icons to display
suit_icons = ["♦","♣","♥","♠"]

# aliases for value number to make code more readable
# starting at one to keep values accurate
# other cards are only the number, there is no need for aliases
JACK = 11
QUEEN = 12
KING = 13
ACE = 14

# icons to display
value_icons = ["", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A" ]

# aliases for game types
# staring at 0 to use and array index if needed
POKER = 0

HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIRS = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8
ROYAL_FLUSH = 9

WIN = 0
LOSE = 1
TIE = 2

class Card:
    suit = 0
    value = 14
    def __init__(self, suit, value):
        if not 0 <= suit <= 3:
            raise Exception("suit must be one of the numbers: 0 - Hearts; 1 - Spades; 2 - Clubs; 3 - Diamonds;")
        self.suit = suit
        if not 2 <= value <= 14:
            raise Exception("value must be one a number between 2 and 14 (including 2 and 14)")
        self.value = value

    def __eq__(self, other):
        return self.suit == other.suit and self.value == other.value

    def __repr__(self):
        return f"[{value_icons[self.value - 1]:>2}|{suit_icons[self.suit]}]"

class OnePair:

    def __init__(self, card1, card2):
        if card1.value != card2.value:
            raise Exception("A pair must be made of 2 cards whith the same value")
        self.card1 = card1
        self.card2 = card2

    def compare(self, other):
        if self.card1.value > other.card1.value:
            return WIN
        if self.card1.value < other.card1.value:
            return LOSE
        else:
            return TIE

class TwoPairs:

    def __init__(self, card1, card2, card3, card4):
        if card1.value < card3.value:
            self.pair1 = OnePair(card1, card2)
            self.pair2 = OnePair(card3, card4)
        else:
            self.pair2 = OnePair(card1, card2)
            self.pair1 = OnePair(card3, card4)

    def compare(self, other):
        if self.pair2.card1.value > other.pair2.card1.value:
            return WIN
        elif self.pair2.card1.value < other.pair2.card1.value:
            return LOSE
        elif self.pair1.card1.value > other.pair1.card1.value:
            return WIN
        elif self.pair1.card1.value < other.pair1.card1.value:
            return LOSE
        else:
            return TIE

class TheeOfAKind:

    def __init__(self, card1, card2, card3):
        if card1.value != card2.value or card2.value != card3.value:
            raise Exception("three of a kind must have three cards with the same value")
        self.card1 = card1
        self.card2 = card2
        self.card3 = card3

    def compare(self, other):
        if self.card1.value > other.card1.value:
            return WIN
        return LOSE

class FourOfAKind:

    def __init__(self, card1, card2, card3, card4):
        if card1.value != card2.value or card2.value != card3.value or card4.value:
            raise("four or a kind must have four cards with the same value")
        self.card1 = card1
        seld.card2 = card2
        self.card3 = card3
        self.card4 = card4

    def compare(self, other):
        if self.card1.value > other.card1.value:
            return WIN
        return LOSE

class Straight:

    def __init__(self, cards):
        if len(cards) != 5:
            raise Exception("straight must be made out of five sequential cards")
        cards = sorted(self.cards, key=lambda card: card.value)
        is_valid = True
        for i in range(0, 5):
            if cards[i] + 1 != cards[i + 1]:
                is_valid = False
        values = [card.value for card in cards]
        if values == [14, 2, 3, 4, 5]:
            is_valid = True
        if not is_valid:
            raise Exception("straight must be made out of five sequential cards")
        self.card1 = cards[0]
        self.card2 = cards[1]
        self.card3 = cards[2]
        self.card4 = cards[3]
        self.card5 = cards[4]

#    def compare(self, other):
#        if self.card1.value 

class Flush:

    def __init__(self, cards):
        if len(cards) != 5 or not (cards[0] == cards[1] == cards[2] == cards[3] == cards[4]):
            raise Exception("flush must be made out of five cards of same suit")
        self.cards

class CardContainer:

    def __init__(self):
        self.cards = []

    def add_card(self, card):
        if card not in self.cards:
            self.cards.append(card)

    def remove_card_by_index(self, index):
        if not 0 <= index < len(self.cards):
            return
        del self.cards[index]

    def remove_card_by_value(self, card):
        try:
            self.cards.remove(card)
        except:
            return

class Deck(CardContainer):

    def __init__(self):
        super().__init__()
        for suit in range(0, 4):
            for value in range(1, 14):
                super().add_card(Card(suit, value))

    def shuffle(self):
        shuffle(self.cards)

class Hand(CardContainer):

    def __init__(self, cards=[]):
        super().__init__()
        if len(cards) != 5:
            raise Exception("A hand needs exactly 5 cards to be valid")
            return
        for card in cards:
            super().add_card(card)
        if len(self.cards) != 5:
            raise Exception("A hand needs exactly 5 distintic cards to be valid")
            return
        self.hand_data = None
        self.hand_type = self.analyse_hand()

    def analyse_hand(self):
        sorted_cards = sorted(self.cards, key=lambda card: card.value)
        self.cards = sorted_cards
        suits = [card.suit for card in sorted_cards]
        values = [card.value for card in sorted_cards]
        different_suits = Counter(suits)


        is_flush = len(different_suits) == 1

        is_straight = True
        for i in range(0, 4):
            if values[i] + 1 != values[i+1]:
                is_straight = False

        if values == [2, 3, 4, 5, 14]:
            is_straight = True

        if is_straight and is_flush and values == [10, 11, 12, 13, 14]:
            self.royal_flush = different_suits[0]
            return ROYAL_FLUSH

        if is_straight and is_flush:
            return STRAIGHT_FLUSH

        for i in range(0, 5):
            if values.count(values[i]) == 4:
                return FOUR_OF_A_KIND

        has_three_of_a_kind = False
        for i in range(0, 5):
            print(values.count(values[i]))
            if values.count(values[i]) == 3:
                has_three_of_a_kind = True

        pairs = []
        for i in range(0, 5):
            if values.count(values[i]) == 2:
                if not values[i] in pairs:
                    pairs.append(values[i])

        if has_three_of_a_kind and len(pairs) == 1:
            return FULL_HOUSE

        if is_flush:
            return FLUSH

        if is_straight:
            return STRAIGHT

        if has_three_of_a_kind:
            return THREE_OF_A_KIND

        if len(pairs) == 2:
            return TWO_PAIRS

        if len(pairs) == 1:
            return ONE_PAIR

        self.hand_data = Card(suits[4], values[4])
        return HIGH_CARD

    def swap_card(self, old_card, new_card):
        if type(old_card) != Card or type(new_card) != Card:
            print("a")
            return
        if old_card == new_card:
            print("b")
            return
        if not old_card in self.cards:
            print("c")
            return
        self.cards.remove(old_card)
        self.cards.append(new_card)
        self.analyse_hand()

    def __repr__(self):
        output =     "+================== HAND ==================+\n|  "
        for card in self.cards:
            output += f"[{value_icons[card.value - 1]:>2}|{suit_icons[card.suit]}]  "
        output += "|\n+==========================================+"
        return output

card = Card(3, 14)
print(card)

try:
    cards = []
    for i in range(0, 5):
        value = int(input("Enter the card value:\n_> "))
        suit = int(input("Enter the card suit:\n_> "))
        cards.append(Card(suit, value))

    hand = Hand(cards)
except Exception as e:
    print("**** ERROR ****\n", e, sep="")
    quit()

print(hand)
print(hand.hand_type)
print(hand.hand_data)
