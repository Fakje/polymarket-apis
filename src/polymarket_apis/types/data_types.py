from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator

from .common import Base, EmptyString, EthAddress, Keccak256


class GQLPosition(Base):
    user: EthAddress
    token_id: str
    complementary_token_id: str
    condition_id: Keccak256
    outcome_index: int
    balance: Decimal

    @model_validator(mode="before")
    def _flatten(cls, values):
        asset = values.get("asset")
        if isinstance(asset, dict):
            if "id" in asset:
                values.setdefault("token_id", asset["id"])
            if "complement" in asset:
                values.setdefault("complementary_token_id", asset["complement"])
            condition = asset.get("condition")
            if isinstance(condition, dict) and "id" in condition:
                values.setdefault("condition_id", condition["id"])
            if "outcomeIndex" in asset:
                values.setdefault("outcome_index", asset["outcomeIndex"])
            values.pop("asset", None)
        return values

    @field_validator("balance", mode="before")
    @classmethod
    def _parse_balance(cls, value):
        if isinstance(value, str):
            value = int(value)
        return Decimal(value) / Decimal(10**6)


class Position(Base):
    # User identification
    proxy_wallet: EthAddress = Field(alias="proxyWallet")

    # Asset information
    token_id: str = Field(alias="asset")
    complementary_token_id: str = Field(alias="oppositeAsset")
    condition_id: Keccak256 = Field(alias="conditionId")
    outcome: str
    complementary_outcome: str = Field(alias="oppositeOutcome")
    outcome_index: int = Field(alias="outcomeIndex")

    # Position details
    size: Decimal
    avg_price: Decimal = Field(alias="avgPrice")
    current_price: Decimal = Field(alias="curPrice")
    redeemable: bool

    # Financial metrics
    initial_value: Decimal = Field(alias="initialValue")
    current_value: Decimal = Field(alias="currentValue")
    cash_pnl: Decimal = Field(alias="cashPnl")
    percent_pnl: Decimal = Field(alias="percentPnl")
    total_bought: Decimal = Field(alias="totalBought")
    realized_pnl: Decimal = Field(alias="realizedPnl")
    percent_realized_pnl: Decimal = Field(alias="percentRealizedPnl")

    # Event information
    title: str
    slug: str
    icon: str
    event_slug: str = Field(alias="eventSlug")
    end_date: datetime = Field(alias="endDate")
    negative_risk: bool = Field(alias="negativeRisk")

    @field_validator("end_date", mode="before")
    def handle_empty_end_date(cls, v):
        if v == "":
            return datetime(2099, 12, 31, tzinfo=UTC)
        return v


class Trade(Base):
    # User identification
    proxy_wallet: EthAddress = Field(alias="proxyWallet")

    # Trade details
    side: Literal["BUY", "SELL"]
    token_id: str = Field(alias="asset")
    condition_id: Keccak256 = Field(alias="conditionId")
    size: Decimal
    price: Decimal
    timestamp: datetime

    # Event information
    title: str
    slug: str
    icon: str
    event_slug: str = Field(alias="eventSlug")
    outcome: str
    outcome_index: int = Field(alias="outcomeIndex")

    # User profile
    name: str
    pseudonym: str
    bio: str
    profile_image: str = Field(alias="profileImage")
    profile_image_optimized: str = Field(alias="profileImageOptimized")

    # Transaction information
    transaction_hash: Keccak256 = Field(alias="transactionHash")


class Activity(Base):
    # User identification
    proxy_wallet: EthAddress = Field(alias="proxyWallet")

    # Activity details
    timestamp: datetime
    condition_id: Keccak256 | EmptyString = Field(alias="conditionId")
    type: Literal["TRADE", "SPLIT", "MERGE", "REDEEM", "REWARD", "CONVERSION"]
    size: Decimal
    usdc_size: Decimal = Field(alias="usdcSize")
    price: Decimal
    asset: str
    side: str | None
    outcome_index: int = Field(alias="outcomeIndex")

    # Event information
    title: str
    slug: str
    icon: str
    event_slug: str = Field(alias="eventSlug")
    outcome: str

    # User profile
    name: str
    pseudonym: str
    bio: str
    profile_image: str = Field(alias="profileImage")
    profile_image_optimized: str = Field(alias="profileImageOptimized")

    # Transaction information
    transaction_hash: Keccak256 = Field(alias="transactionHash")


class Holder(Base):
    # User identification
    proxy_wallet: EthAddress = Field(alias="proxyWallet")

    # Holder details
    token_id: str = Field(alias="asset")
    amount: Decimal
    outcome_index: int = Field(alias="outcomeIndex")

    # User profile
    name: str
    pseudonym: str
    bio: str
    profile_image: str = Field(alias="profileImage")
    profile_image_optimized: str = Field(alias="profileImageOptimized")
    display_username_public: bool = Field(alias="displayUsernamePublic")


class HolderResponse(Base):
    # Asset information
    token_id: str = Field(alias="token")

    # Holders list
    holders: list[Holder]


class ValueResponse(Base):
    # User identification
    proxy_wallet: EthAddress = Field(alias="proxyWallet")

    # Value information
    value: Decimal


class User(Base):
    proxy_wallet: EthAddress = Field(alias="proxyWallet")
    name: str
    bio: str
    profile_image: str = Field(alias="profileImage")
    profile_image_optimized: str = Field(alias="profileImageOptimized")


class UserMetric(User):
    amount: Decimal
    pseudonym: str


class UserRank(User):
    amount: Decimal
    rank: int


class MarketValue(Base):
    condition_id: Keccak256 = Field(alias="market")
    value: Decimal


class EventLiveVolume(Base):
    total: Optional[Decimal]
    markets: Optional[list[MarketValue]]
