from .agents import Orchestrator, UNIVERSE


class ScannerEngine:

    def __init__(self):
        self.orch = Orchestrator()

    def breakout_scan(self):

        results = []

        for symbol in UNIVERSE:

            try:

                data = self.orch.analyze(symbol)

                technical = data.get(
                    "technical", {}
                )

                pattern = data.get(
                    "pattern", {}
                )

                if (

                    technical.get(
                        "direction"
                    ) == "BULLISH"

                    and

                    pattern.get(
                        "direction"
                    ) == "BULLISH"

                    and

                    data.get(
                        "decision"
                    ) in [
                        "BUY",
                        "WATCH_BUY"
                    ]

                ):

                    results.append(data)

            except Exception:
                continue

        results.sort(

            key=lambda x:
            x["bullish_score"]
            -
            x["bearish_score"],

            reverse=True

        )

        return results[:10]

    def momentum_scan(self):

        results = []

        for symbol in UNIVERSE:

            try:

                data = self.orch.analyze(symbol)

                technical = data.get(
                    "technical", {}
                )

                if (

                    technical.get(
                        "five_day_return",
                        0
                    ) > 3

                    and

                    technical.get(
                        "twenty_day_return",
                        0
                    ) > 5

                ):

                    results.append(data)

            except Exception:
                continue

        results.sort(

            key=lambda x:
            x["technical"].get(
                "five_day_return",
                0
            ),

            reverse=True

        )

        return results[:10]

    def rsi_scan(self):

        results = []

        for symbol in UNIVERSE:

            try:

                data = self.orch.analyze(symbol)

                rsi = data.get(
                    "technical",
                    {}
                ).get(
                    "rsi",
                    0
                )

                if 50 <= rsi <= 70:

                    results.append(data)

            except Exception:
                continue

        return results[:10]