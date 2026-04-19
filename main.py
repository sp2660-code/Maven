import pygame
import RPi.GPIO as GPIO
from gpiozero import TonalBuzzer, LED
from gpiozero.tones import Tone
import time
import random

# ==========================================
# 1. HARDWARE INITIALIZATION
# ==========================================
led_gain = LED(27)
led_loss = LED(23)
buzzer = TonalBuzzer(18)
error_timer = 0

current_week = 1
current_month = 1
current_year = 2026

biweekly_salary = 2000
weekly_expenses = 750

current_quiz = None
quiz_feedback = ""
quiz_timer = 0
loss = 0


MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


GPIO.setmode(GPIO.BCM)
ROW_PINS = [5, 6, 13, 19]
COL_PINS = [12, 16, 20, 21]
KEYPAD = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

for row in ROW_PINS:
    GPIO.setup(row, GPIO.OUT)
    GPIO.output(row, GPIO.HIGH)
for col in COL_PINS:
    GPIO.setup(col, GPIO.IN, pull_up_down=GPIO.PUD_UP)

key_cooldown = 0

def get_key():
    global key_cooldown
    if time.time() < key_cooldown:
        return None
    for i, row in enumerate(ROW_PINS):
        GPIO.output(row, GPIO.LOW)
        for j, col in enumerate(COL_PINS):
            if GPIO.input(col) == GPIO.LOW:
                GPIO.output(row, GPIO.HIGH)
                key_cooldown = time.time() + 0.4 # Slightly longer debounce
                return KEYPAD[i][j]
        GPIO.output(row, GPIO.HIGH)
    return None

def safe_draw_image(img, pos, fallback_color):
    if img:
        screen.blit(img, pos)
    else:
        # Draw a placeholder rectangle if the image is missing
        pygame.draw.rect(screen, fallback_color, (pos[0], pos[1], 50, 50))


def trigger_feedback(is_gain):
    if is_gain:
        led_gain.on()
        buzzer.play(Tone("C5"))
    else:
        led_loss.on()
        buzzer.play(Tone("A3"))
    pygame.time.set_timer(pygame.USEREVENT + 1, 600)

# ==========================================
# 2. GAME ENGINE CLASSES
# ==========================================
class Player:
    def __init__(self):
        self.net_worth = 1000
        self.cash = 0
        self.savings = 0
        self.investments = 0
        self.market_trend = ""

    def select_path(self, choice):
        if choice == '1': # Aggressive
            self.cash, self.savings, self.investments = 1000, 1500, 2000
        elif choice == '2': # Middle
            self.cash, self.savings, self.investments = 2000, 1250, 1250
        elif choice == '3': # Spree
            self.cash, self.savings, self.investments = 3500, 500, 500
        self.net_worth = self.cash + self.savings + self.investments

    def update_market(self):
        old_val = self.investments
        change_pct = random.uniform(-0.02, 0.0225)
        self.investments *= (1 + change_pct)
        self.investments = round(self.investments, 2)

        if self.investments > old_val:
            self.market_trend = "UP"
        else:
            self.market_trend = "DOWN"

        return change_pct


player = Player()
game_state = "START_SCREEN"
current_event = None
event_result = ""

# One event will be selected every month
events_pool = [
    {"text": "Car breakdown! Cost: $500. Press (A) to pay", "type": "EXPENSE", "cost": 500},
    {"text": "Utility Spike! AC was running too high this week. Press (A) to pay", "type": "EXPENSE", "cost": 200},
    {"text": "Market Drop! Invests down 10%. Press (D) to Continue", "type": "MARKET_LOSS", "pct": 0.10},
    {"text": "Market Rally! Invests up 15%. Press (D) to Continue", "type": "MARKET_GAIN", "pct": 0.15}
]


# Quiz questions will occur on for 3/4 weeks of the month

quiz_pool = [
    {
        "q": "What is the primary benefit of a 401(k) with an employer match?",
        "options": ["A: Instant 100% Return", "B: Lower Credit Risk", "C: Higher Liquidity", "D: Fixed Interest"],
        "ans": "A",
        "loss": 1000,
        "explanation": "An employer match is essentially free money. If you put in $1 and they match it, you've doubled your money instantly."
    },
    {
        "q": "Which of these is considered a 'Liquid Asset'?",
        "options": ["A: Real Estate", "B: 2-Year CD", "C: Savings Account", "D: Retirement Fund"],
        "ans": "C",
        "loss": 1000,
        "explanation": "Liquidity refers to how quickly you can turn an asset into cash. You can withdraw from savings immediately."
    },
    {
        "q": "If inflation is 4% and your savings pay 1%, your purchasing power is:",
        "options": ["A: Increasing", "B: Decreasing", "C: Staying Even", "D: Doubling"],
        "ans": "B",
        "loss": 1000,
        "explanation": "If prices rise faster (4%) than your money grows (1%), your money buys less over time."
    },
    {
        "q": "What is the primary risk of carrying a high balance on a credit card?",
        "options": ["A: High Interest", "B: Flat Fees", "C: Lower Taxes", "D: Bonus Points"],
        "ans": "A",
        "loss": 1000,
        "explanation": "Credit cards have high APRs; carrying a balance means you pay compound interest on your debt, which grows quickly."
    },
    {
        "q": "What does a 'bear market' typically signify?",
        "options": ["A: Rising Prices", "B: Falling Prices", "C: Market Stability", "D: High Trading"],
        "ans": "B",
        "loss": 1000,
        "explanation": "A bear market occurs when stock prices fall by 20% or more from recent highs, usually due to economic pessimism."
    },
    {
        "q": "Which of these contributes most to your FICO credit score?",
        "options": ["A: Annual Income", "B: Payment History", "C: Job Title", "D: Bank Balance"],
        "ans": "B",
        "loss": 1000,
        "explanation": "Payment history accounts for 35% of your FICO score. Even one missed payment can significantly lower it."
    },
    {
        "q": "What is a 'Premium' in the context of insurance?",
        "options": ["A: The Deductible", "B: Monthly Cost", "C: Coverage Limit", "D: Payout Amount"],
        "ans": "B",
        "loss": 1000,
        "explanation": "The premium is the fixed amount you pay (usually monthly) to keep your insurance policy active."
    },
    {
        "q": "Investing in a 'Target Date Fund' is primarily based on what?",
        "options": ["A: Market Trends", "B: Retirement Year", "C: Risk Tolerance", "D: Stock Price"],
        "ans": "B",
        "loss": 1000,
        "explanation": "These funds automatically adjust your asset allocation to become more conservative as you get closer to your retirement year."
    },
    {
        "q": "What is the main purpose of an 'Emergency Fund'?",
        "options": ["A: Buying Stocks", "B: Vacation Money", "C: Unplanned Costs", "D: Down Payments"],
        "ans": "C",
        "loss": 1000,
        "explanation": "An emergency fund should ideally cover 3-6 months of living expenses to protect you from job loss or repairs."
    },
    {
        "q": "In a 1040 tax form, what does 'Adjusted Gross Income' (AGI) represent?",
        "options": ["A: Total Wealth", "B: Income after Tax", "C: Income minus Deductions", "D: Refund Amount"],
        "ans": "C",
        "loss": 1000,
        "explanation": "AGI is your total gross income minus specific 'above-the-line' deductions; it determines your tax bracket."
    },
    {
        "q": "What happens if you withdraw from a traditional 401(k) before age 59.5?",
        "options": ["A: 10% Penalty", "B: No Penalty", "C: Interest Bonus", "D: Instant Profit"],
        "ans": "A",
        "loss": 1000,
        "explanation": "Early withdrawals are generally subject to income tax plus a 10% federal penalty for non-qualified distributions."
    },
    {
        "q": "What is 'Diversification' in an investment portfolio?",
        "options": ["A: Picking one Stock", "B: Spreading Assets", "C: Shorting Stocks", "D: Day Trading"],
        "ans": "B",
        "loss": 1000,
        "explanation": "Diversification reduces risk by spreading your money across different sectors, like tech, energy, and bonds."
    },
    {
        "q": "What is 'Overdraft Protection' usually associated with?",
        "options": ["A: Higher Interest", "B: Hidden Bank Fees", "C: Credit Limits", "D: Investment Gains"],
        "ans": "B",
        "loss": 1000,
        "explanation": "Banks often charge a fee for 'protecting' you from a declined transaction if your balance hits zero."
    }

]


def advance_time():
    global current_week, current_month, current_year, event_result, current_quiz, current_event, game_state
    
    # 1. Weekly Burn
    player.cash -= weekly_expenses
    player.update_market()

    
    # 2. Regular Bi-Weekly Salary
    if current_week == 2 or current_week == 4:
        player.cash += biweekly_salary

    # 3. ANNUAL BONUSES
    # December (Month 12, Week 4): Year-End Bonus
    if current_month == 12 and current_week == 4:
        # Instead of just adding to cash, trigger a special event
        game_state = "BONUS_DECISION"
        current_event = {"text": "Annual Bonus: $3500! Where to put it?", "amt": 3500}

    # April (Month 4, Week 2): Tax Refund
    elif current_month == 4 and current_week == 2:
        refund = 1200
        player.cash += refund
        event_result = f"TAX REFUND: +${refund}!"
        trigger_feedback(True)

    # 4. Calendar Rollover
    current_week += 1
    if current_week > 4:
        current_week = 1
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    if (current_week == 4):
        current_event = random.choice(events_pool)
        game_state = 'PLAYING'
    else:
        current_quiz = random.choice(quiz_pool)
        game_state = 'QUIZ_TIME'

    player.net_worth = player.cash + player.savings + player.investments
    if player.net_worth <= 0:
        game_state = "GAME_OVER"


# ==========================================
# 3. PYGAME DISPLAY
# ==========================================
pygame.init()
WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

font_small = pygame.font.Font(None, 40) 
font_main = pygame.font.Font(None, 45)
font_large = pygame.font.Font(None, 70)

#Load in UI image elements
img_save = pygame.image.load("SAVE.png").convert_alpha()
img_save = pygame.transform.scale(img_save, (125, 85)) # Adjust size as needed

img_green = pygame.image.load("GREEN.png").convert_alpha()
img_green = pygame.transform.scale(img_green, (75, 75)) # Adjust size as needed

img_red = pygame.image.load("RED.png").convert_alpha()
img_red = pygame.transform.scale(img_red, (75, 75)) # Adjust size as needed


def draw_ui():
    screen.fill((15, 15, 25))
    # HUD Bar
    pygame.draw.rect(screen, (40, 40, 60), (0, 0, WIDTH, 110))
    # Render Stats
    net_txt = font_main.render(f"NET WORTH: ${int(player.net_worth)}", True, (0, 255, 150))
    cash_txt = font_small.render(f"CASH: ${player.cash} | SAVINGS: ${player.savings} | INVESTED: ${int(player.investments)}", True, (255, 255, 255))
    
    date_str = f"{MONTH_NAMES[current_month-1]} - Week {current_week}"
    date_txt = font_main.render(date_str, True, (255, 215, 0)) # Gold color

    screen.blit(net_txt, (20, 15))
    screen.blit(cash_txt, (20, 60))
    screen.blit(date_txt, (450, 15))

    if player.market_trend == "UP":
        screen.blit(img_green, (700, 25))
    elif player.market_trend == "DOWN":
        screen.blit(img_red, (700, 25))

    
    

def draw_text_wrapped(text, font, color, x, y, max_width):
    words = text.split(' ')
    lines = []
    current_line = []

    for word in words:
        # Check how wide the line would be if we added this word
        test_line = ' '.join(current_line + [word])
        w, h = font.size(test_line)
        
        if w < max_width:
            current_line.append(word)
        else:
            # Line is too wide, start a new one
            lines.append(' '.join(current_line))
            current_line = [word]
    
    # Add the final line
    lines.append(' '.join(current_line))

    # Render each line onto the screen
    for i, line in enumerate(lines):
        rendered_line = font.render(line, True, color)
        screen.blit(rendered_line, (x, y + (i * (h + 5)))) # h + 5 is line spacing


# ==========================================
# 4. MAIN LOOP
# ==========================================
running = True
while running:
    draw_ui()
    key = get_key()
   
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.USEREVENT + 1:
            led_gain.off(); led_loss.off(); buzzer.stop()
    

    if game_state == "START_SCREEN":
        title = font_large.render("MAVEN", True, (255, 215, 0))
        instr = font_main.render("1: Aggressive | 2: Middle | 3: Spree", True, (200, 200, 200))
        screen.blit(title, (WIDTH//2 - 100, 180))
        screen.blit(instr, (WIDTH//2 - 280, 280))
       
        if key in ['1', '2', '3']:
            player.select_path(key)
            current_quiz = random.choice(quiz_pool)
            game_state = "QUIZ_TIME"

    elif game_state == "PLAYING":
        # Render the current event box
        if key == 'C':
            game_state = "TRANSFER_TYPE"
            key = None


        pygame.draw.rect(screen, (30, 30, 50), (50, 150, 700, 250), border_radius=15)
        ev_txt = font_main.render(current_event["text"], True, (255, 255, 100))
        draw_text_wrapped(current_event["text"], font_main, (255, 255, 100), 80, 190, 640)
        res_txt = font_main.render(event_result, True, (0, 255, 0))
        screen.blit(res_txt, (80, 300))
        hint_txt = font_main.render("Press (C) to Transfer Money", True, (150, 150, 150))
        screen.blit(hint_txt, (80, 360))

        if key:
            etype = current_event["type"]
            
                

            if etype == "EXPENSE":
                if key == 'A': # Pay Cash
                    advance_time()
                    player.cash -= current_event["cost"]
                    event_result = f"-${current_event['cost']} from Cash!"
                    trigger_feedback(False)
                    pygame.display.flip(); time.sleep(1.2)
                    current_event = random.choice(events_pool); event_result = ""

            elif etype == "INCOME":

                if key == 'A':
                    advance_time()
                    player.savings += current_event["amt"]
                    event_result = "Savings boosted!"
                    trigger_feedback(True)
                elif key == 'B':
                    advance_time()
                    player.investments += current_event["amt"]
                    event_result = "Investments boosted!"
                    trigger_feedback(True)
                if key in ['A', 'B']:
                    pygame.display.flip(); time.sleep(1.2)
                    current_event = random.choice(events_pool); event_result = ""

            elif etype in ["MARKET_LOSS", "MARKET_GAIN"]:
                if key == 'D':
                    advance_time()
                    change = player.investments * current_event["pct"]
                    if etype == "MARKET_LOSS":
                        player.investments -= change
                        trigger_feedback(False)
                    else:
                        player.investments += change
                        trigger_feedback(True)
                    current_event = random.choice(events_pool); event_result = ""
    elif game_state == "TRANSFER_TYPE":
        # Render Transfer UI
        pygame.draw.rect(screen, (50, 30, 70), (50, 130, 700, 320), border_radius=15)
        title = font_main.render("SELECT TRANSFER TYPE", True, (255, 255, 255))

        opts = [
            "1: Cash -> Investment",
            "2: Investment -> Cash",
            "3: Cash -> Savings",
            "4: Savings -> Cash",
            "D: Cancel"
        ]
        screen.blit(title, (80, 150))
        for i, opt in enumerate(opts):
            txt = font_main.render(opt, True, (200, 200, 255))
            screen.blit(txt, (80, 200 + (i * 45)))

        if key in ['1', '2', '3', '4']:
            transfer_direction = key
            input_buffer = "" # Reset buffer for typing
            game_state = "TRANSFER_AMOUNT"
        elif key == 'D':
            game_state = "PLAYING"

    elif game_state == "TRANSFER_AMOUNT":
        pygame.draw.rect(screen, (30, 60, 50), (50, 130, 700, 320), border_radius=15)
        dir_labels = {
            '1': "Cash -> Investment",
            '2': "Investment -> Cash",
            '3': "Cash -> Savings",
            '4': "Savings -> Cash"
        }

        current_label = dir_labels.get(transfer_direction, "Transfer")

        type_txt = font_main.render(f"Mode: {current_label}", True, (0, 255, 255))
        prompt = font_main.render("ENTER AMOUNT & PRESS #", True, (255, 255, 255))
        amount_display = font_large.render(f"${input_buffer}", True, (255, 215, 0))
        cancel_hint = font_main.render("Press * to Clear | D to Cancel", True, (150, 150, 150))

        screen.blit(type_txt, (80, 150))      # Displays what they are doing
        screen.blit(prompt, (80, 210))        # Instructions
        screen.blit(amount_display, (WIDTH//2 - 50, 280)) # The typed number
        screen.blit(cancel_hint, (80, 380))   # Helpful hint


        if key and key.isdigit() and len(input_buffer) < 7:        
            input_buffer += key # Add number to string
        
        elif key == '*': # Clear button
            input_buffer = ""
        
        elif key == "D":
            game_state = "TRANSFER_TYPE"
            
        elif key == '#': # Enter button
            amt = int(input_buffer) if input_buffer else 0
            success = False


            # Logic for moving the money
            if transfer_direction == '1' and player.cash >= amt:
                player.cash -= amt; player.investments += amt; success = True
            elif transfer_direction == '2' and player.investments >= amt:
                player.investments -= amt; player.cash += amt; success = True
            elif transfer_direction == '3' and player.cash >= amt:
                player.cash -= amt; player.savings += amt; success = True
            elif transfer_direction == '4' and player.savings >= amt:
                player.savings -= amt; player.cash += amt; success = True

            trigger_feedback(success)
            if success:
                game_state = "PLAYING" # Go back to game
            else:
                error_timer = time.time() + 1.0
                game_state = "ERROR_SCREEN"
    elif game_state == "ERROR_SCREEN":
        # Draw a red warning box
        pygame.draw.rect(screen, (150, 0, 0), (100, 200, 600, 150), border_radius=15)
        err_txt = font_large.render("INSUFFICIENT FUNDS", True, (255, 255, 255))
        screen.blit(err_txt, (WIDTH//2 - 260, 245))

        # Check if 1 second has passed
        if time.time() > error_timer:
            input_buffer = ""  # Optional: clear their bad entry
            game_state = "TRANSFER_AMOUNT"
    elif game_state == "BONUS_DECISION":
        pygame.draw.rect(screen, (0, 80, 0), (50, 150, 700, 250), border_radius=15)
        title = font_main.render(current_event["text"], True, (255, 255, 255))
        screen.blit(title, (80, 180))
        
        # Display Choice Images (using your A and B icons)
        screen.blit(img_save, (100, 280)) # Label this "Savings"
        #2nd image

        if key == 'A':
            player.savings += current_event["amt"]
            game_state = "PLAYING"
        elif key == 'B':
            player.investments += current_event["amt"]
            game_state = "PLAYING"

    elif game_state == "QUIZ_TIME":
        # Draw Quiz Box
        pygame.draw.rect(screen, (20, 40, 80), (50, 130, 700, 320), border_radius=15)
        
        # 1. Wrap and draw the question
        draw_text_wrapped(current_quiz["q"], font_main, (255, 215, 0), 80, 150, 640)
        
        # 2. Draw the options
        for i, opt in enumerate(current_quiz["options"]):
            opt_txt = font_main.render(opt, True, (255, 255, 255))
            screen.blit(opt_txt, (80, 230 + (i * 40)))

        # 3. Handle Keypad Input (A, B, C, or D)
        if key in ['A', 'B', 'C', 'D']:
            if key == current_quiz["ans"]:
                quiz_feedback = f"CORRECT!"
                trigger_feedback(True)
            else:
                loss = current_quiz["loss"]
                player.cash -= loss
                quiz_feedback = f"INCORRECT! You lose -${loss}"
                trigger_feedback(False)
            
            # Show feedback briefly then advance time
            game_state = "QUIZ_RESULT"
            quiz_timer = time.time() + 1.5

    elif game_state == "QUIZ_RESULT":
        pygame.draw.rect(screen, (10, 10, 25), (150, 200, 500, 100), border_radius=15)
        draw_text_wrapped(quiz_feedback, font_large, (255, 255, 255), 180, 230, 500)
        
        if time.time() > quiz_timer:
            game_state = "EXPLANATION" # Move the clock forward
    elif game_state == "EXPLANATION":
        pygame.draw.rect(screen, (20, 20, 40), (40, 120, 720, 340), border_radius=15)
        
        # 1. THE QUESTION (Header)
        head_q = font_main.render("THE QUESTION:", True, (255, 215, 0)) # Gold
        screen.blit(head_q, (70, 140))
        
        # 2. Draw the original question text
        draw_text_wrapped(current_quiz["q"], font_main, (200, 200, 200), 70, 175, 660)
        
        # 3. THE LESSON (Header)
        head_l = font_main.render("THE LESSON:", True, (0, 255, 150)) # Green-ish
        screen.blit(head_l, (70, 260))
        
        # 4. Draw the explanation text
        draw_text_wrapped(current_quiz["explanation"], font_main, (255, 255, 255), 70, 295, 660)
        
        # 5. Interaction Prompt
        hint_txt = font_main.render("Press (D) to Continue", True, (100, 100, 100))
        screen.blit(hint_txt, (70, 420))

        if key == 'D':
            advance_time() # Move to next week
    
    elif game_state == "GAME_OVER":
        # 1. Fill screen with a dark red tint
        screen.fill((40, 5, 5))
        
        # 2. Main "DEBT TRAP" Heading
        # Using your VT323 font for that big retro look
        lose_title = font_large.render("BANKRUPTCY DECLARED", True, (255, 50, 50))
        screen.blit(lose_title, (WIDTH//2 - 280, 100))
        
        # 3. Final Stats
        # Show them how long they survived
        survival_txt = font_small.render(f"SURVIVED UNTIL: {MONTH_NAMES[current_month-1]} {current_year}", True, (255, 255, 255))
        screen.blit(survival_txt, (WIDTH//2 - 200, 200))
        
        # 4. The "Lesson"
        reason_txt = "Your debts and expenses have swallowed your assets. New Brunswick isn't cheap!"
        draw_text_wrapped(reason_txt, font_small, (200, 200, 200), 160, 280, 600)
        
        # 5. Restart Instruction
        retry_txt = font_small.render("PRESS (1) TO TRY AGAIN", True, (255, 215, 0))
        screen.blit(retry_txt, (WIDTH//2 - 150, 400))

        # 6. Reset Logic
        if key == '1':
            # Reset player and time variables
            player = Player() 
            current_week = 1
            current_month = 1
            current_year = 2026
            game_state = "START_SCREEN"
        

    # Auto-update Net Worth
    player.net_worth = player.cash + player.savings + player.investments

    pygame.display.flip()
    clock.tick(30)

GPIO.cleanup()