from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import AliasChoices, Field, field_validator

from ..types.clob_types import MakerOrder, OrderBookSummary, TickSize
from ..types.common import Base, EthAddress, Keccak256, TimeseriesPoint
from ..types.gamma_types import Comment, Reaction


# wss://ws-subscriptions-clob.polymarket.com/ws/market types


class PriceChange(Base):
    best_ask: Decimal = Field(validation_alias=AliasChoices("ba", "best_ask"))
    best_bid: Decimal = Field(validation_alias=AliasChoices("bb", "best_bid"))
    price: Decimal = Field(validation_alias=AliasChoices("p", "price"))
    size: Decimal = Field(validation_alias=AliasChoices("s", "size"))
    side: Literal["BUY", "SELL"] = Field(validation_alias=AliasChoices("si", "side"))
    token_id: str = Field(validation_alias=AliasChoices("a", "asset_id"))
    hash: str = Field(validation_alias=AliasChoices("h", "hash"))


class PriceChanges(Base):
    condition_id: Keccak256 = Field(validation_alias=AliasChoices("m", "market"))
    price_changes: list[PriceChange] = Field(
        validation_alias=AliasChoices("pc", "price_changes")
    )
    timestamp: datetime = Field(validation_alias=AliasChoices("t", "timestamp"))


class TickSizeChange(Base):
    token_id: str = Field(alias="asset_id")
    condition_id: Keccak256 = Field(alias="market")
    old_tick_size: TickSize
    new_tick_size: TickSize


class LastTradePrice(Base):
    price: Decimal
    size: Decimal
    side: Literal["BUY", "SELL"]
    token_id: str = Field(alias="asset_id")
    condition_id: Keccak256 = Field(alias="market")
    fee_rate_bps: Decimal


class OrderBookSummaryEvent(OrderBookSummary):
    event_type: Literal["book"]


class PriceChangeEvent(PriceChanges):
    event_type: Literal["price_change"]


class TickSizeChangeEvent(TickSizeChange):
    timestamp: datetime
    event_type: Literal["tick_size_change"]


class LastTradePriceEvent(LastTradePrice):
    timestamp: datetime
    event_type: Literal["last_trade_price"]

class EventMessage(Base):
    id: str
    ticker: str
    slug: str
    title: str
    description: str

class MarketResolvedEvent(Base):
    market_id: Keccak256 = Field(alias="id")
    condition_id: Keccak256 = Field(alias="market")
    question: str
    market: str
    slug: str
    description: str
    assets_ids: list[str] = Field(alias="token_ids")
    outcomes: list[str]
    winning_asset_id: str
    winning_outcome: str
    event_message: EventMessage
    timestamp: datetime
    event_type: Literal["market_resolved"]

class BestBidAskEvent(Base):
    market: str
    asset_id: str
    best_bid: Decimal
    best_ask: Decimal
    spread: Decimal
    timestamp: datetime = Field(validation_alias=AliasChoices("t", "timestamp"))
    event_type: Literal["best_bid_ask"]




# wss://ws-subscriptions-clob.polymarket.com/ws/user types


class OrderEvent(Base):
    token_id: str = Field(alias="asset_id")
    condition_id: Keccak256 = Field(alias="market")
    order_id: Keccak256 = Field(alias="id")
    associated_trades: Optional[list[str]] = None  # list of trade ids which
    maker_address: EthAddress
    order_owner: str = Field(alias="owner")  # api key of order owner
    event_owner: Optional[str] = Field(None, alias="owner")  # api key of event owner

    price: Decimal
    side: Literal["BUY", "SELL"]
    size_matched: Decimal
    original_size: Decimal
    outcome: str
    order_type: Literal["GTC", "GTD", "FOK", "FAK"]

    created_at: datetime
    expiration: Optional[datetime] = None
    timestamp: Optional[datetime] = None  # time of event

    event_type: Optional[Literal["order"]] = None
    type: Literal["PLACEMENT", "UPDATE", "CANCELLATION"]

    status: Literal["LIVE", "CANCELED", "MATCHED"]

    @field_validator("expiration", mode="before")
    def validate_expiration(cls, v):
        if v == "0":
            return None
        return v


class TradeEvent(Base):
    token_id: str = Field(alias="asset_id")
    condition_id: Keccak256 = Field(alias="market")
    taker_order_id: Keccak256
    maker_orders: list[MakerOrder]
    trade_id: str = Field(alias="id")
    trade_owner: Optional[str] = Field(None, alias="owner")  # api key of trade owner
    event_owner: str = Field(alias="owner")  # api key of event owner

    price: Decimal
    size: Decimal
    side: Literal["BUY", "SELL"]
    outcome: str

    last_update: datetime  # time of last update to trade
    matchtime: Optional[datetime] = None  # time trade was matched
    timestamp: Optional[datetime] = None  # time of event

    event_type: Optional[Literal["trade"]] = None
    type: Optional[Literal["TRADE"]] = None

    status: Literal["MATCHED", "MINED", "CONFIRMED", "RETRYING", "FAILED"]


# wss://ws-live-data.polymarket.com types


# Payload models
class ActivityTrade(Base):
    token_id: str = Field(
        alias="asset"
    )  # ERC1155 token ID of conditional token being traded
    condition_id: str = Field(
        alias="conditionId"
    )  # Id of market which is also the CTF condition ID
    event_slug: str = Field(alias="eventSlug")  # Slug of the event
    outcome: str  # Human readable outcome of the market
    outcome_index: int = Field(alias="outcomeIndex")  # Index of the outcome
    price: Decimal  # Price of the trade
    side: Literal["BUY", "SELL"]  # Side of the trade
    size: Decimal  # Size of the trade
    slug: str  # Slug of the market
    timestamp: datetime  # Timestamp of the trade
    title: str  # Title of the event
    transaction_hash: str = Field(alias="transactionHash")  # Hash of the transaction
    proxy_wallet: str = Field(alias="proxyWallet")  # Address of the user proxy wallet
    icon: str  # URL to the market icon image
    name: str  # Name of the user of the trade
    bio: str  # Bio of the user of the trade
    pseudonym: str  # Pseudonym of the user
    profile_image: str = Field(alias="profileImage")  # URL to the user profile image
    profile_image_optimized: Optional[str] = Field(None, alias="profileImageOptimized")


class Request(Base):
    request_id: str = Field(alias="requestId")  # Unique identifier for the request
    proxy_address: str = Field(alias="proxyAddress")  # Proxy address
    user_address: str = Field(alias="userAddress")  # User address
    condition_id: Keccak256 = Field(
        alias="market"
    )  # Id of market which is also the CTF condition ID
    token_id: str = Field(
        alias="token"
    )  # ERC1155 token ID of conditional token being traded
    complement_token_id: str = Field(
        alias="complement"
    )  # Complement ERC1155 token ID of conditional token being traded
    state: Literal[
        "STATE_REQUEST_EXPIRED",
        "STATE_USER_CANCELED",
        "STATE_REQUEST_CANCELED",
        "STATE_MAKER_CANCELED",
        "STATE_ACCEPTING_QUOTES",
        "STATE_REQUEST_QUOTED",
        "STATE_QUOTE_IMPROVED",
    ]  # Current state of the request
    side: Literal["BUY", "SELL"]  # Indicates buy or sell side
    price: Decimal  # Price from in/out sizes
    size_in: Decimal = Field(alias="sizeIn")  # Input size of the request
    size_out: Decimal = Field(alias="sizeOut")  # Output size of the request
    expiry: Optional[datetime] = None


class Quote(Base):
    quote_id: str = Field(alias="quoteId")  # Unique identifier for the quote
    request_id: str = Field(alias="requestId")  # Associated request identifier
    proxy_address: str = Field(alias="proxyAddress")  # Proxy address
    user_address: str = Field(alias="userAddress")  # User address
    condition_id: Keccak256 = Field(
        alias="condition"
    )  # Id of market which is also the CTF condition ID
    token_id: str = Field(
        alias="token"
    )  # ERC1155 token ID of conditional token being traded
    complement_token_id: str = Field(
        alias="complement"
    )  # Complement ERC1155 token ID of conditional token being traded
    state: Literal[
        "STATE_REQUEST_EXPIRED",
        "STATE_USER_CANCELED",
        "STATE_REQUEST_CANCELED",
        "STATE_MAKER_CANCELED",
        "STATE_ACCEPTING_QUOTES",
        "STATE_REQUEST_QUOTED",
        "STATE_QUOTE_IMPROVED",
    ]  # Current state of the quote
    side: Literal["BUY", "SELL"]  # Indicates buy or sell side
    size_in: Decimal = Field(alias="sizeIn")  # Input size of the quote
    size_out: Decimal = Field(alias="sizeOut")  # Output size of the quote
    expiry: Optional[datetime] = None


class CryptoPriceSubscribe(Base):
    data: list[TimeseriesPoint]
    symbol: str


class CryptoPriceUpdate(TimeseriesPoint):
    symbol: str
    full_accuracy_value: str


class AggOrderBookSummary(OrderBookSummary):
    min_order_size: Decimal
    tick_size: TickSize
    neg_risk: bool


class LiveDataClobMarket(Base):
    token_ids: list[str] = Field(alias="asset_ids")
    condition_id: Keccak256 = Field(alias="market")
    min_order_size: Decimal
    tick_size: TickSize
    neg_risk: bool


# Event models
class ActivityTradeEvent(Base):
    payload: ActivityTrade
    timestamp: datetime
    type: Literal["trades"]
    topic: Literal["activity"]


class ActivityOrderMatchEvent(Base):
    payload: ActivityTrade
    timestamp: datetime
    type: Literal["orders_matched"]
    topic: Literal["activity"]


class CommentEvent(Base):
    payload: Comment
    timestamp: datetime
    type: Literal["comment_created", "comment_removed"]
    topic: Literal["comments"]


class ReactionEvent(Base):
    payload: Reaction
    timestamp: datetime
    type: Literal["reaction_created", "reaction_removed"]
    topic: Literal["comments"]


class RequestEvent(Base):
    payload: Request
    timestamp: datetime
    type: Literal[
        "request_created", "request_edited", "request_canceled", "request_expired"
    ]
    topic: Literal["rfq"]


class QuoteEvent(Base):
    payload: Quote
    timestamp: datetime
    type: Literal["quote_created", "quote_edited", "quote_canceled", "quote_expired"]
    topic: Literal["rfq"]


class CryptoPriceUpdateEvent(Base):
    payload: CryptoPriceUpdate
    timestamp: datetime
    connection_id: str
    type: Literal["update"]
    topic: Literal["crypto_prices", "crypto_prices_chainlink"]


class CryptoPriceSubscribeEvent(Base):
    payload: CryptoPriceSubscribe
    timestamp: datetime
    type: Literal["subscribe"]
    topic: Literal["crypto_prices", "crypto_prices_chainlink"]


class LiveDataOrderBookSummaryEvent(Base):
    payload: list[AggOrderBookSummary] | AggOrderBookSummary
    timestamp: datetime
    connection_id: str
    type: Literal["agg_orderbook"]
    topic: Literal["clob_market"]


class LiveDataPriceChangeEvent(Base):
    payload: PriceChanges
    timestamp: datetime
    connection_id: str
    type: Literal["price_change"]
    topic: Literal["clob_market"]


class LiveDataLastTradePriceEvent(Base):
    payload: LastTradePrice
    timestamp: datetime
    connection_id: str
    type: Literal["last_trade_price"]
    topic: Literal["clob_market"]


class LiveDataTickSizeChangeEvent(Base):
    payload: TickSizeChange
    timestamp: datetime
    connection_id: str
    type: Literal["tick_size_change"]
    topic: Literal["clob_market"]


class MarketStatusChangeEvent(Base):
    payload: LiveDataClobMarket
    timestamp: datetime
    connection_id: str
    type: Literal["market_created", "market_resolved"]
    topic: Literal["clob_market"]


class LiveDataOrderEvent(Base):
    payload: OrderEvent
    timestamp: datetime
    connection_id: str
    type: Literal["order"]
    topic: Literal["clob_user"]


class LiveDataTradeEvent(Base):
    payload: TradeEvent
    timestamp: datetime
    connection_id: str
    type: Literal["trade"]
    topic: Literal["clob_user"]


class ErrorEvent(Base):
    message: str
    connection_id: str = Field(alias="connectionId")
    request_id: str = Field(alias="requestId")
