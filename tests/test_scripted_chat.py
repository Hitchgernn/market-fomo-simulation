from backend.engine.model import StockMarketModel


def test_scripted_chat_defaults_to_enabled_mode():
    model = StockMarketModel(rng=1)
    assert model.chat_mode == "scripted"


def test_scripted_chat_generates_bearish_message_for_market_maker_dump():
    model = StockMarketModel(chat_mode="scripted", rng=1)
    model.latest_events = []
    model.last_shock_volume = 144
    model.market_regime = "shock"

    message = model.generate_scripted_chat()

    assert any(word in message.message for word in ["dump", "cutloss", "panik"])


def test_scripted_chat_generates_bullish_message_for_positive_imbalance():
    model = StockMarketModel(chat_mode="scripted", rng=1)
    model.last_order_imbalance = 0.25
    model.current_price = 106
    model.previous_price = 100
    model.market_regime = "normal"

    message = model.generate_scripted_chat()

    assert any(word in message.message for word in ["moon", "naik", "buyer"])


def test_scripted_chat_generates_sideways_message_for_flat_market():
    model = StockMarketModel(chat_mode="scripted", rng=1)
    model.last_order_imbalance = 0.0
    model.current_price = 100
    model.previous_price = 100
    model.market_regime = "normal"

    message = model.generate_scripted_chat()

    assert any(word in message.message for word in ["sideways", "tunggu", "breakout"])
