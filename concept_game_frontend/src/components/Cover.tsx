import React, {useState} from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import VideogameAssetIcon from '@material-ui/icons/VideogameAsset';


const useStyles = makeStyles((theme) => ({
    description: {
        marginBottom: "2em",
        fontSize: 20,
    },
}));

interface CoverProps {
    startGame: boolean;
    setStart : (startGame : boolean ) => void;
}


export const Cover : React.FC<CoverProps> = (props: CoverProps) => {
  const classes = useStyles();

  function handleStartButton() {
    props.setStart( true );
  }

  return (
    <>
        <div className={classes.description}>
            <h1>Concept Game</h1>

            Concept Game is a two player collaborative game, where players guess the concept
            for a list of words. <br/><br/>

            The player pair receives a score when they mutually agree on a word or expression which describes the words.
            <br/><br/>

            E.g., "apple, orange" can belong to "fruit".
        </div>
        <Button
            variant="contained"
            color="primary"
            // className={classes.button}
            endIcon={<VideogameAssetIcon/>}
            onClick={handleStartButton}
        >
        Play
        </Button>
    </>
);
}
