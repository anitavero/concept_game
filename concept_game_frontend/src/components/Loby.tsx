import React from 'react';

import { makeStyles } from '@material-ui/core/styles';
import CircularProgress from '@material-ui/core/CircularProgress';

const useStyles = makeStyles((theme) => ({
    waitingMessage: {
        marginBottom: "2em",
    },
}));

export const Loby : React.FC<{}> =  () => {
  const classes = useStyles();

  return (
    <>
        <div className={classes.waitingMessage}>Waiting for the other player.</div>
        <CircularProgress />
    </>
);
}
