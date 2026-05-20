"""change_money_fields_to_numeric

Revision ID: 002
Revises: 001
Create Date: 2026-05-19

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # wallets: balance, frozen_balance
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)
    op.alter_column('wallets', 'frozen_balance',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)

    # shops: min_order_amount, delivery_fee
    op.alter_column('shops', 'min_order_amount',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)
    op.alter_column('shops', 'delivery_fee',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)

    # products: price, original_price
    op.alter_column('products', 'price',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=False)
    op.alter_column('products', 'original_price',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)

    # orders: total_amount, discount_amount, delivery_fee
    op.alter_column('orders', 'total_amount',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=False)
    op.alter_column('orders', 'discount_amount',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)
    op.alter_column('orders', 'delivery_fee',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=True)

    # order_items: price
    op.alter_column('order_items', 'price',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=False)

    # rider_earnings: amount
    op.alter_column('rider_earnings', 'amount',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=False)

    # withdrawal_records: amount
    op.alter_column('withdrawal_records', 'amount',
                    existing_type=sa.Float(),
                    type_=sa.Numeric(10, 2),
                    existing_nullable=False)


def downgrade() -> None:
    # wallets
    op.alter_column('wallets', 'frozen_balance',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('wallets', 'balance',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=True)

    # shops
    op.alter_column('shops', 'delivery_fee',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('shops', 'min_order_amount',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=True)

    # products
    op.alter_column('products', 'original_price',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('products', 'price',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=False)

    # orders
    op.alter_column('orders', 'delivery_fee',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('orders', 'discount_amount',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('orders', 'total_amount',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=False)

    # order_items
    op.alter_column('order_items', 'price',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=False)

    # rider_earnings
    op.alter_column('rider_earnings', 'amount',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=False)

    # withdrawal_records
    op.alter_column('withdrawal_records', 'amount',
                    existing_type=sa.Numeric(10, 2),
                    type_=sa.Float(),
                    existing_nullable=False)
