import random

# aliases for suit numbers to make code more readable
# staring at 0 to use and array index if needed
DIAMONDS = 0
CLUBS = 1
HEARTS = 2
SPADES = 4

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

NOTHING = 0
HIGH_CARD = 1
ONE_PAIR = 2
TWO_PAIR = 3
THREE_OF_A_KIND = 4
STRAIGHT = 5
FLUSH = 6
FULL_HOUSE = 7
FOUR_OF_A_KIND = 8
STRAIGHT_FLUSH = 9
ROYAL_FLUSH = 10

class Pair:

    def __init__(self, card1, card2):
        if card1.value != card2.value:
            raise Exception("pairs must have two cards with the same VALUE")
        self.card1 = card1
        self.card2 = card2

    def get_value(self):
        return self.card1.value

    def get_suits(self):
        return (self.card1.suit, self.card2.suit)

class TheeOfAKind:

    def __init__(self, self, card1, card2, card3):
        if card1.value != card2.value or card2.value != card3.value:
            raise Exception("three of a kind must be made out of three card with the same value")
        self.card1 = card1
        self.card2 = card2
        self.card3 = card3

    def get_value(self):
        return self.card1.value

    def get_suits(self):
        return (self.card1.suit, self.card2.suit, self.card3.suit)

class FourOfAKind:

    def init(self, card1, card2, card3, card4):
        if card1.value != card2.value or card2.value != card3.value or card3.value != card4.value:
            raise Exception("four of a kind must be made out of four card with the same value")
        

class Card:
    suit = 0
    value = 14
    def __init__(self, suit, value):
        if not 0 <= suit <= 3:
            raise Exception("suit must be one of the numbers: 0 - Hearts; 1 - Spades; 2 - Clubs; 3 - Diamonds;")
        self.suit = suit
        if not 2 <= value <= 14:
            raise Exception("value must be one a number between 1 and 13 (including 1 and 13)")
        self.value = value

    def __eq__(self, other):
        return self.suit == other.suit and self.value == self.value

    def display(self):
        print(f"[{value_icons[self.value - 1]:>2}|{suit_icons[self.suit]}]")

class CardContainer:

    def __init__(self):
        self.cards = []

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
        for suit in range(0, 4):
            for value in range(1, 14):
                self.cards.append(Card(suit, value))

    def shuffle(self):
        shuffle(self.cards)

class Hand(CardContainer):

    def __init__(self, cards=[]):
        if len(cards) != 5:
            raise Exception("A hand needs exactly 5 cards to be valid")
            return
        self.cards = cards
        self.high_card = False
        self.pair_1 = False
        self.pair_2 = False
        self.three = False
        self.four = False
        self.flush = False
        self.straight = False
        self.full_house = False
        self.straight_flush = False
        self.royal_flush = False
        self.hand_type = self.analyse_hand()

    def analyse_hand(self):
        sorted_cards = sorted(self.cards, key=lambda card: card.value)
        suits = [card.suit for card in sorted_cards]
        values = [card.value for card in sorted_cards]

        different_suits = Counter(suits)

        is_flush = len(different_suits) == 1

        is_straigth = True
        for i in range(0, 5):
            if values[i] + 1 != values[i+1]:
                is_straight = False
        if values = [14, 2, 3, 4, 5]:
            is_straight = True
        if is_straight and is_flush and values = [10, 11, 12, 13, 14]:
            self.royal_flush = different_suits[0]
            return ROYAL_FLUSH

        if is_straight and is_flush:
            return STRAIGHT_FLUSH

        for i in range(0, 5):
            if values.count(values[i]) == 4:
                return FOUR_OF_A_KIND

        has_three_of_a_kind = False
        for i in range(0, 5):
            if values.count(values[i]) == 3:
                has_three_equals = True

        pairs = []
        for i in range(0, 5):
            if values.count(values[i]) == 2:
                if not values[i] in pairs:
                    pairs.append(values[i])

        if has_three_equals and len(pairs) == 1:
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
            return PAIR

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

    def __repr__(self):
        output = "+================== HAND ==================+\n|  "
        for card in self.cards:
            output += f"[{value_icons[card.value - 1]:>2}|{suit_icons[card.suit]}]  "
        output += "|\n+==========================================+"
        return output

card = Card(3, 14)
card.display()

hand = Hand([Card(3, 14), Card(0, 10), Card(1, 2), Card(2, 14), Card(0, 14)])
hand.swap_card(Card(0, 10), Card(1, 14))
print(hand)
