import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from flask import Flask, send_from_directory, request
from flask_cors import CORS, cross_origin
import json
from .StateManager import StateManager


class WebServer(QThread):
    app = Flask(__name__, static_folder=os.path.curdir)
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'
    scoreboard = None

    def __init__(self, parent=None, scoreboard=None) -> None:
        super().__init__(parent)
        WebServer.scoreboard = scoreboard
        self.host_name = "0.0.0.0"
        self.port = 5000

    @app.route("/ruleset")
    def main():
        data = {}

        data["ruleset"] = StateManager.Get(f"score.ruleset", {})

        # Add webserver base path
        data.update({
            "basedir": os.path.abspath(".")
        })

        # Add player names
        teams = [1, 2]
        if WebServer.scoreboard.teamsSwapped:
            teams.reverse()

        for i, t in enumerate(teams):
            if StateManager.Get(f"score.team.{i+1}.teamName"):
                data.update({
                    f"p{t}": StateManager.Get(f"score.team.{i+1}.teamName")
                })
            else:
                names = [p.get("name") for p in StateManager.Get(
                    f"score.team.{i+1}.player", {}).values() if p.get("name")]

                data.update({
                    f"p{t}": " / ".join(names)
                })

        # Add set data
        data.update({
            "best_of": StateManager.Get(f"score.best_of"),
            "match": StateManager.Get(f"score.match"),
            "phase": StateManager.Get(f"score.phase"),
            "state": StateManager.Get(f"score.stage_strike.state", {})
        })

        return data

    @app.route('/post', methods=['POST'])
    def post_route():
        StateManager.Set(f"score.stage_strike", json.loads(request.get_data()))
        return "OK"

    @app.route('/score', methods=['POST'])
    def post_score():
        score = json.loads(request.get_data())
        WebServer.scoreboard.signals.UpdateSetData.emit(score)
        return "OK"

    # Ticks score of Team specified up by 1 point
    @app.route('/team<team>-scoreup')
    def team_scoreup(team):
        if team == "1":
            WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_left").setValue(
                WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_left").value() + 1)
        else:
            WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_right").setValue(
                WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_right").value() + 1)
        return "OK"

    # Ticks score of Team specified down by 1 point
    @app.route('/team<team>-scoredown')
    def team_scoredown(team):
        if team == "1":
            if WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_left").value() - 1 < 1:
                WebServer.scoreboard.scoreColumn.findChild(
                    QSpinBox, "score_left").setValue(0)
            else:
                WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_left").setValue(
                    WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_left").value() - 1)
        else:
            if WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_right").value() - 1 < 1:
                WebServer.scoreboard.scoreColumn.findChild(
                    QSpinBox, "score_right").setValue(0)
            else:
                WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_right").setValue(
                    WebServer.scoreboard.scoreColumn.findChild(QSpinBox, "score_right").value() - 1)
        return "OK"

    # Dynamic endpoint to allow flexible sets of information
    # Ex. http://192.168.1.2:5000/set?best-of=5
    #
    # Test Scenario that was used
    # Ex. http://192.168.4.34:5000/set?best-of=5&phase=Top 32&match=Winners Finals
    @app.route('/set')
    def set_route():
        # Best Of argument
        # best-of=<Best Of Amount>
        if request.args.get('best-of') is not None:
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'bestOf': request.args.get(
                        'best-of', default='0', type=int)})
                )
            )

        # Phase argument
        # phase=<Phase Name>
        if request.args.get('phase') is not None:
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'tournament_phase': request.args.get(
                        'phase', default='Pools', type=str)})
                )
            )

        # Match argument
        # match=<Match Name>
        if request.args.get('match') is not None:
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'round_name': request.args.get(
                        'match', default='Pools', type=str)})
                )
            )

        # Players argument
        # players=<Amount of Players>
        if request.args.get('players') is not None:
            WebServer.scoreboard.playerNumber.setValue(
                request.args.get('players', default=1, type=int))

        # Characters argument
        # characters=<Amount of Characters>
        if request.args.get('characters') is not None:
            WebServer.scoreboard.charNumber.setValue(
                request.args.get('characters', default=1, type=int))

        # Losers argument
        # losers=<True/False>&team=<Team Number>
        if request.args.get('losers') is not None:
            losers = request.args.get('losers', default=False, type=bool)
            WebServer.scoreboard.signals.UpdateSetData.emit(
                json.loads(
                    json.dumps({'team' + request.args.get('team',
                               default='1', type=str) + 'losers': bool(losers)})
                )
            )
        return "OK"

    # Swaps teams
    @app.route('/swap-teams')
    def swap_teams():
        WebServer.scoreboard.SwapTeams()
        return "OK"

    # Resets scores
    @app.route('/reset-scores')
    def reset_scores():
        WebServer.scoreboard.ResetScore()
        return "OK"

    # Resets scores, match, phase, and losers status
    @app.route('/reset-match')
    def reset_match():
        WebServer.scoreboard.ClearScore()
        WebServer.scoreboard.scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        return "OK"

    # Resets all values
    @app.route('/clear-all')
    def clear_all():
        WebServer.scoreboard.ClearScore()
        WebServer.scoreboard.scoreColumn.findChild(
            QSpinBox, "best_of").setValue(0)
        WebServer.scoreboard.playerNumber.setValue(1)
        WebServer.scoreboard.charNumber.setValue(1)
        return "OK"

    @app.route('/', defaults=dict(filename=None))
    @app.route('/<path:filename>', methods=['GET', 'POST'])
    @cross_origin()
    def test(filename):
        filename = filename or 'stage_strike_app/build/index.html'
        print(os.path.abspath("."), filename)
        return send_from_directory(os.path.abspath("."), filename)

    def run(self):
        self.app.run(host=self.host_name, port=self.port,
                     debug=True, use_reloader=False)
