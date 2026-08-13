class TradePlanAgent:

    def generate(
        self,
        price,
        risk,
        account_size=100000,
        risk_per_trade_pct=1
    ):

        stop_loss_pct = float(
            risk.get(
                "stop_loss_pct",
                2
            )
        )

        target_pct = float(
            risk.get(
                "target_pct",
                4
            )
        )

        entry = round(
            price,
            2
        )

        stop_loss = round(
            entry *
            (
                1 -
                stop_loss_pct / 100
            ),
            2
        )

        target = round(
            entry *
            (
                1 +
                target_pct / 100
            ),
            2
        )

        risk_per_share = round(
            entry -
            stop_loss,
            2
        )

        reward_per_share = round(
            target -
            entry,
            2
        )

        risk_reward = 0.0

        if risk_per_share > 0:

            risk_reward = round(
                reward_per_share /
                risk_per_share,
                2
            )

        max_risk = (

            account_size *

            (
                risk_per_trade_pct / 100
            )

        )

        quantity = 0

        if risk_per_share > 0:

            quantity = int(
                max_risk /
                risk_per_share
            )

        capital_used = round(
            quantity *
            entry,
            2
        )

        return {

            "entry":
                entry,

            "stop_loss":
                stop_loss,

            "target":
                target,

            "risk_per_share":
                risk_per_share,

            "reward_per_share":
                reward_per_share,

            "risk_reward":
                risk_reward,

            "account_size":
                account_size,

            "risk_per_trade":
                max_risk,

            "recommended_quantity":
                quantity,

            "capital_used":
                capital_used

        }