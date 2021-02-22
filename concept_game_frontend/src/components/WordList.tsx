import React from 'react';

import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import Zoom from '@material-ui/core/Zoom';

const useStyles = makeStyles((theme) => ({
    card: {
        width: "100%",
    },
    title: {
        fontSize: 14,
      },
}));

interface WordListProps {
    words: string[];
    match: boolean;
}

export const WordList : React.FC<WordListProps> =  (props: WordListProps) => {
  const classes = useStyles();

  return (
    <Zoom in={props.match} timeout={100} mountOnEnter unmountOnExit>
        <Card className={classes.card}>
            <CardContent>
            <Typography className={classes.title} color="textSecondary" gutterBottom>
                Guess the concept for these words:
            </Typography>
            <Typography variant="body1" component="p">
                {props.words}
            </Typography>
            </CardContent>
        </Card>
    </Zoom>
);
}
