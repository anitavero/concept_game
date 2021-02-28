import React, {useState, useEffect, useRef} from 'react';
import './App.css';

import CssBaseline from '@material-ui/core/CssBaseline';

import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';

import { Loby } from './components/Loby';
import { Cover } from './components/Cover';
import { Game } from './components/Game';
import { ScoreDisplay } from './components/ScoreDisplay';

const useStyles = makeStyles((theme) => ({
  paper: {
    marginTop: theme.spacing(4),
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  submit: {
    margin: theme.spacing(3, 0, 2),
  },
}));


function App() {
  const classes = useStyles();

  const [words, setWords] = useState<string[]>([]);
  const [guesses, setGuesses] = useState<string[]>([]);
  const [readyToGuess, setReadyToGuess] = useState<boolean>(false);
  const [score, setScore] = useState<number>(0);
  const [match, setMatch] = useState<boolean>(false);
  const [startGame, setStartGame] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string|null>(null);


  const ws = useRef<WebSocket|null>(null);


  useEffect(() => {
        console.log('Mount useEffect', sessionId);
        if(sessionId) {
            console.log("Game is happening");
            ws.current = new WebSocket("ws://" + location.hostname + ":6789/session/" + sessionId);

            ws.current.onmessage = function (event) {
              const data = JSON.parse(event.data);
              switch (data.type) {
                  case 'words':
                      setGuesses([]);
                      setReadyToGuess(true);
                      setMatch(true);
                      setWords(data.words);
                      break;
                  case 'score':
                      setScore(data.score);
                      setMatch(false);
                      break;
                  case 'other_player_abandoned_game':
                      setReadyToGuess(false);
                      setStartGame(false);  // Go to Cover
                      setScore(0);
                      console.log(data);
                      setSessionId(null);
                      break;
                  default:
                      console.error(
                          "unsupported event", data);
              }
            };
      }
      else{
        ws.current = new WebSocket("ws://" + location.hostname + ":6789" + "/queue");
        ws.current.onmessage = function (event) {
            const data = JSON.parse(event.data);
            switch (data.type) {
                case 'users':
                    break;
                case 'session':
                    setSessionId(data.session_id);
                    break;
                default:
                    console.error(
                        "unsupported event", data);
            }
        }
    };

    return () => {
        console.log('Unmount useEffect');
      if(ws.current) {
        ws.current.close();
      }
    }
  }, [sessionId]);


  function handleStart(start: boolean) {
      setStartGame(start);
      if (ws.current) {
          ws.current.send(
              JSON.stringify({'action': 'play'}));
      }
  }

  function handleGuess(guess: string) {
    setGuesses(guesses.concat(guess));
    if(ws.current){
      ws.current.send(
        JSON.stringify({'action': 'guess', 'guess': guess}));
    }
  }
    {
      return (
          <Container component="main" maxWidth="xs">

              <ScoreDisplay score={score}/>

              <CssBaseline/>
              <div className={classes.paper}>
                  {startGame
                      ? ((readyToGuess
                          ? <Game words={words} match={match} guesses={guesses} sendGuess={handleGuess}/>
                          : <Loby/>))
                      : (<Cover startGame={startGame} setStart={handleStart}/>)
                  }

              </div>
          </Container>
      );
  }
}

export default App;
