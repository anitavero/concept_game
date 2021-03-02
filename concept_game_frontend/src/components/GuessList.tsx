import React from 'react';

import Chip from '@material-ui/core/Chip';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import Container from '@material-ui/core/Container';
import DoneIcon from '@material-ui/icons/Done';

const useStyles = makeStyles((theme) => ({
  guessList: {
    '& > *': {
        margin: theme.spacing(0.5),
      },
  }
}));

interface GuessListProps {
    guesses: string[];
    matching_guess: boolean;
}

export const GuessList : React.FC<GuessListProps> =  (props: GuessListProps) => {
  const classes = useStyles();

  if(props.guesses.length==0){
    return (
        <div>You didn't make any guesses yet.</div>
    );
  }else{
    return (
        <>
            <div>Your guesses:</div>
            <div className={classes.guessList}>
            {props.guesses.map((guess, index) =>
                (props.matching_guess ?
                   <Chip icon={<DoneIcon/>} key={index} label={guess} color="secondary" />
                   : <Chip label={guess} key={index} />)
            )}
            </div>
        </>
    );
  }
}
