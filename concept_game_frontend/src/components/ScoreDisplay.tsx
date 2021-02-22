import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import Badge from '@material-ui/core/Badge';
import StarIcon from '@material-ui/icons/Star';

const useStyles = makeStyles((theme) => ({
    score: {
        position: "absolute",
        top:"20px",
        right: "20px",
    },
}));

interface ScoreDisplayProps {
    score: number;
}

export const ScoreDisplay : React.FC<ScoreDisplayProps> =  (props: ScoreDisplayProps) => {
  const classes = useStyles();

  if(props.score>0){
  return (
    <Badge className={classes.score} badgeContent={props.score} color="primary">
        <StarIcon />
    </Badge>
  );
  } else{
      return <></>;
  }
}
