import random
from collections import deque


# How many recent regime labels to retain per symbol for the
# "regime timeline" plot. Bounded for the same reason price/return
# history is bounded elsewhere -- a very long run shouldn't leak
# memory.
REGIME_HISTORY_MAXLEN = 5_000


# Regime definitions. Each regime multiplies/offsets the base
# MarketData parameters (drift added on top of order-flow impact,
# vol_multiplier scales the per-step gaussian noise, reversion_mult
# scales how hard price is pulled back to the long-run anchor).
#
# min_duration/max_duration are in simulation steps -- a regime is
# sampled to last somewhere in that range before a transition is
# even considered, so regimes don't flicker step-to-step (which would
# make "regime-aware" strategies meaningless -- they need enough
# steps within one regime to actually detect and act on it).
REGIME_PARAMS = {
    "trending_up": {
        "drift": 0.12,
        "vol_multiplier": 1.0,
        "reversion_multiplier": 0.3,
        "min_duration": 40,
        "max_duration": 150,
    },
    "trending_down": {
        "drift": -0.12,
        "vol_multiplier": 1.0,
        "reversion_multiplier": 0.3,
        "min_duration": 40,
        "max_duration": 150,
    },
    "mean_reverting": {
        "drift": 0.0,
        "vol_multiplier": 0.8,
        "reversion_multiplier": 1.6,
        "min_duration": 60,
        "max_duration": 200,
    },
    "low_volatility": {
        "drift": 0.0,
        "vol_multiplier": 0.35,
        "reversion_multiplier": 1.0,
        "min_duration": 60,
        "max_duration": 200,
    },
    "high_volatility": {
        "drift": 0.0,
        "vol_multiplier": 2.5,
        "reversion_multiplier": 0.7,
        "min_duration": 20,
        "max_duration": 80,
    },
    "panic": {
        "drift": -0.9,
        "vol_multiplier": 4.0,
        "reversion_multiplier": 0.15,
        "min_duration": 5,
        "max_duration": 20,
    },
    "recovery": {
        "drift": 0.35,
        "vol_multiplier": 1.8,
        "reversion_multiplier": 0.4,
        "min_duration": 15,
        "max_duration": 50,
    },
}


# Transition weights: from each regime, the relative likelihood of
# moving to each other regime once its duration expires. Panic is
# reachable only from high_volatility (a vol spike escalating into a
# crash) rather than out of nowhere, and is always followed by
# recovery -- mirroring how real market stress cycles unfold, rather
# than a memoryless jump straight back to calm.
REGIME_TRANSITIONS = {
    "trending_up": {"trending_up": 0.25, "mean_reverting": 0.35, "low_volatility": 0.2, "high_volatility": 0.2},
    "trending_down": {"trending_down": 0.2, "mean_reverting": 0.3, "high_volatility": 0.3, "low_volatility": 0.2},
    "mean_reverting": {"mean_reverting": 0.3, "trending_up": 0.2, "trending_down": 0.2, "low_volatility": 0.2, "high_volatility": 0.1},
    "low_volatility": {"low_volatility": 0.35, "mean_reverting": 0.3, "trending_up": 0.175, "trending_down": 0.175},
    "high_volatility": {"high_volatility": 0.25, "panic": 0.15, "mean_reverting": 0.2, "trending_up": 0.2, "trending_down": 0.2},
    "panic": {"recovery": 1.0},
    "recovery": {"mean_reverting": 0.4, "low_volatility": 0.3, "trending_up": 0.3},
}


class MarketRegimeEngine:
    """
    Drives regime switching per symbol.

    This is the fix for Problem #6 ("momentum always loses") and a
    big part of Problems #8/#12 (equity curves and price formation
    too smooth): the original MarketData process was a single
    stationary Ornstein-Uhlenbeck process with one fixed reversion
    strength. That's *inherently* a mean-reverting process -- there
    was never a regime in which a trend-following strategy could have
    a genuine statistical edge, so momentum was mathematically
    guaranteed to lose money over any sufficiently long run
    regardless of parameter tuning. Tuning constants can't fix a
    strategy whose edge doesn't exist anywhere in the simulated world.

    Instead of hard-coding "momentum wins X% of the time", this
    engine periodically switches the market between qualitatively
    different regimes (trending, mean-reverting, calm, volatile,
    panic/crash, recovery) with realistic persistence. MarketData
    consumes the active regime's drift/volatility/reversion
    parameters every step. Momentum earns its edge honestly during
    trending_up/trending_down regimes (there genuinely is a trend to
    follow); mean-reversion earns its edge honestly during
    mean_reverting/low_volatility regimes; nothing is guaranteed to
    dominate every environment, satisfying Problem #6's actual
    requirement rather than just changing who wins on average.
    """

    def __init__(self, symbols=None, seed=None):

        self.symbols = list(symbols or ["AAPL"])

        self._rng = random.Random(seed) if seed is not None else random

        self.current_regime = {}
        self.steps_remaining = {}
        self.regime_history = {}

        for symbol in self.symbols:
            self._start_new_regime(symbol, initial="mean_reverting")


    def _ensure_symbol(self, symbol):

        if symbol not in self.current_regime:
            self._start_new_regime(symbol, initial="mean_reverting")


    def _start_new_regime(self, symbol, initial=None):

        regime = initial or self._rng.choice(list(REGIME_PARAMS.keys()))

        params = REGIME_PARAMS[regime]

        duration = self._rng.randint(
            params["min_duration"],
            params["max_duration"]
        )

        self.current_regime[symbol] = regime
        self.steps_remaining[symbol] = duration

        self.regime_history.setdefault(
            symbol, deque(maxlen=REGIME_HISTORY_MAXLEN)
        )


    def _transition(self, symbol):

        current = self.current_regime[symbol]

        weights = REGIME_TRANSITIONS[current]

        next_regimes = list(weights.keys())
        next_weights = list(weights.values())

        next_regime = self._rng.choices(
            next_regimes,
            weights=next_weights,
            k=1
        )[0]

        self._start_new_regime(symbol, initial=next_regime)


    def step(self, symbol="AAPL"):
        """
        Advances the regime state machine by one simulation step and
        returns the active regime's parameter dict. Call this once
        per symbol per simulation step, before pricing that symbol.
        """

        self._ensure_symbol(symbol)

        self.steps_remaining[symbol] -= 1

        if self.steps_remaining[symbol] <= 0:
            self._transition(symbol)

        self.regime_history[symbol].append(self.current_regime[symbol])

        return REGIME_PARAMS[self.current_regime[symbol]]


    def get_current_regime(self, symbol="AAPL"):

        self._ensure_symbol(symbol)

        return self.current_regime[symbol]


    def get_regime_history(self, symbol="AAPL", count=None):
        """
        Returns the recent sequence of regime labels for a symbol,
        one per simulation step -- what the "regime timeline" plot
        should draw.
        """

        self._ensure_symbol(symbol)

        history = list(self.regime_history[symbol])

        if count is not None:
            return history[-count:]

        return history
