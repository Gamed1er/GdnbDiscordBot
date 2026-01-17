import math

class LevelManager:
    BLANK_LEVEL_DATA = {"xp": 0, "last_talk_time": 0, "last_word": "", "level": 0}

    @staticmethod
    def level_to_xp(x):
        return 18 * x * x - 21 * x + 4  # 18x^2 - 21x + 4
    
    @staticmethod
    def xp_to_level(y):
        if y <= 0: return 0
        return int((21 + math.sqrt(153 + 72 * y)) / 36)

    @staticmethod
    def get_progress_bar(current_xp, next_xp):
        current_xp -= LevelManager.level_to_xp(LevelManager.xp_to_level(next_xp) - 1)
        next_xp -= LevelManager.level_to_xp(LevelManager.xp_to_level(next_xp) - 1)
        
        percentage = min(current_xp / next_xp, 1.0)
        filled = int(10 * percentage)
        return ":green_square:" * filled + ":white_large_square:" * (10 - filled)
    
    @staticmethod
    def check_level_up(xp, xp_gain):
        before_lv = LevelManager.xp_to_level(xp)
        after_lv = LevelManager.xp_to_level(xp + xp_gain)
        return after_lv - before_lv