import React, { useState } from 'react';

import { makeStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';

import { GuessList } from './GuessList';
import { WordList } from './WordList';

const useStyles = makeStyles((theme) => ({
    guessForm: {
        width: "100%",
        marginTop: "3em"
    }
}));

interface GameProps {
    words: string[];
    match: boolean;
    guesses: string[];
    sendGuess : (guess : string ) => void;
}

export const Game : React.FC<GameProps> =  (props: GameProps) => {
  const classes = useStyles();

  const [guess, setGuess] = useState<string>("");


  function handleGuessChange(event : React.ChangeEvent<HTMLInputElement>) {
    setGuess( event.target.value );
  }

  function checkForEnter(event: React.KeyboardEvent<HTMLInputElement> ){
    if(event.key == "Enter"){
        props.sendGuess( guess );
        setGuess( "" );
    }
  }

  return (
    <>
        <WordList words={props.words}
                  match={props.match}/>
        
        <div className={classes.guessForm}>
            <GuessList guesses={props.guesses} matching_guess="" />
    
            <TextField
                variant="outlined"
                margin="normal"
                fullWidth
                label="Type your guess or 'pass' here and press enter."
                name="guess"
                value={guess}
                onChange={handleGuessChange}
                onKeyUp={checkForEnter}
                autoFocus
            />
        </div>
    </>
);
}



//                 