import React, {useState, useEffect, useRef} from 'react';
import './App.css';

import CssBaseline from '@material-ui/core/CssBaseline';

import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import Dialog from '@material-ui/core/Dialog';
import DialogTitle from '@material-ui/core/DialogTitle';

import { Loby } from './components/Loby';
import { Cover } from './components/Cover';
import { Game } from './components/Game';
import { ScoreDisplay } from './components/ScoreDisplay';
import { Timer } from './components/Timer';

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

interface DialogText {
    title: string;
    text: string;
}

function App() {
  const classes = useStyles();

  const [words, setWords] = useState<string[]>([]);
  const [guesses, setGuesses] = useState<string[]>([]);
  const [readyToGuess, setReadyToGuess] = useState<boolean>(false);
  const [score, setScore] = useState<number>(0);
  const [match, setMatch] = useState<boolean>(false);
  const [matchDialogue, setMatchDialogue] = useState<boolean>(false);
  const [startGame, setStartGame] = useState<boolean>(false);
  const [sessionId, setSessionId] = useState<string|null>(null);
  const [dialogText, setDialogText] = useState<DialogText>({title: "Matched with", text: ''});
  const [showTimer, setShowTimer] = useState<boolean>(false);
  const [time, setTime] = useState<number>(40);

  const showDialog = () => setMatchDialogue(true);
  const hideDialog = () => setTimeout(() => setMatchDialogue(false),1500);

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
                      setMatch(false);
                      hideDialog();
                      setWords(data.words);
                      setTime(40);
                      setShowTimer(true);
                      break;
                  case 'score':
                      setShowTimer(false);
                      setScore(data.score);
                      if(data.match != 'timeout') {
                          setDialogText({title: "Matched with", text: data.match});
                          showDialog();
                      }
                      setMatch(true);
                      break;
                  case 'other_player_abandoned_game':
                      setReadyToGuess(false);
                      setStartGame(false);  // Go to Cover
                      setShowTimer(false);
                      setScore(0);
                      console.log(data);
                      setSessionId(null);
                      setDialogText({title: "Other player left", text: ":("});
                      showDialog();
                      hideDialog();
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


  function handleTime(curTime: number) {
      setTime(curTime);
      console.log("TIME", curTime);
      if(curTime == 0 && ws.current){
          ws.current.send(
              JSON.stringify({'action': 'guess', 'guess': "TIMEOUT"}));
      }
  }

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

              {showTimer ? <Timer show={showTimer} time={time} sendTime={handleTime}/> : <></>}

              <CssBaseline/>
              <div className={classes.paper}>
                  {!matchDialogue ?
                          (startGame
                          ? ((readyToGuess
                              ? <Game words={words} match={match} guesses={guesses} sendGuess={handleGuess}/>
                              : <Loby/>))
                          : (<Cover startGame={startGame} setStart={handleStart}/>))
                      : (
                          <Dialog
                              open={matchDialogue}
                              onClose={hideDialog}
                              aria-labelledby="alert-dialog-title"
                              aria-describedby="alert-dialog-description"
                            >
                              <DialogTitle id="alert-dialog-title">{dialogText.title}</DialogTitle>
                              <DialogContent>
                                  <DialogContentText id="alert-dialog-description">
                                      {dialogText.text}
                                  </DialogContentText>
                              </DialogContent>
                          </Dialog>
                      )
                  }

              </div>
          </Container>
      );
  }
}

export default App;
