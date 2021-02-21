import React, {useState, useEffect, useRef} from 'react';
import './App.css';

import CssBaseline from '@material-ui/core/CssBaseline';

import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';

import { Loby } from './components/Loby';
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


  const ws = useRef<WebSocket|null>(null);


  useEffect(() => {
    ws.current = new WebSocket("ws://" + location.hostname + ":6789");
    ws.current.onmessage = function (event) {
        const data = JSON.parse(event.data);
        switch (data.type) {
            case 'words':
                setGuesses([]);
                setReadyToGuess(true);
                setWords(data.words);
                break;
            case 'words':
                  setGuesses([]);
                  setReadyToGuess(true);
                  setWords(data.words);
                  break;
            case 'score':
                  setScore(data.score);
                  break;
            default:
                console.error(
                    "unsupported event", data);
        }
    };

    return () => {
      if(ws.current) {
        ws.current.close();
      }
    }
  }, []);



  /*
  const words: string[] = ["warlord", "drone warfare", "nobel peace prize"];
  const guesses : string[] = [];
  const readyToGuess : boolean = true;
  const score : number = 0;
  */


  function handleGuess(guess: string) {
    setGuesses(guesses.concat(guess));
    if(ws.current){
      ws.current.send(
        JSON.stringify({'action': 'guess', 'guess': guess
      }));
    }
  };

  return (
    <Container component="main" maxWidth="xs">

      <ScoreDisplay score={score} />
      
      <CssBaseline />
      <div className={classes.paper}>

        {readyToGuess ? <Game words={words} guesses={guesses} sendGuess={handleGuess} /> : <Loby />}


      </div>
    </Container>
  );
}

export default App;
