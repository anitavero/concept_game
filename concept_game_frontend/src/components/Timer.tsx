import React from 'react';
import CircularProgress, { CircularProgressProps } from '@material-ui/core/CircularProgress';
import Typography from '@material-ui/core/Typography';
import Box from '@material-ui/core/Box';
import {makeStyles} from "@material-ui/core";


const useStyles = makeStyles((theme) => ({
    timer: {
        position: "absolute",
        top:"20px",
        left: "20px",
    },
}));

function CircularProgressWithLabel(props: CircularProgressProps & { value: number, multiplyer: number }) {
  const classes = useStyles();
    return (
    <Box className={classes.timer}>
      <CircularProgress variant="determinate" {...props} size={60} color="secondary"/>
      <Box
        top={0}
        left={0}
        bottom={0}
        right={0}
        position="absolute"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <Typography variant="h4" component="div" color="textSecondary">
            {Math.round(props.multiplyer * props.value)}
        </Typography>
      </Box>
    </Box>
  );
}

interface TimerProps {
    show: boolean;
    time: number;
    sendTime: (curTime : number ) => void;
}

export const Timer : React.FC<TimerProps> =  (props: TimerProps) => {
  const [progress, setProgress] = React.useState(props.time);

  React.useEffect(() => {
    const timer = setInterval(() => {
      setProgress((prevProgress) => (prevProgress > 0 ? prevProgress - 1 : 0));
      props.sendTime( progress );
    }, 1000);
    return () => {
      clearInterval(timer);
    };
  }, []);

  if(props.show){
  return (<CircularProgressWithLabel value={Math.round((100/props.time) * progress)} multiplyer={props.time/100}/>);
  } else{
      return <></>;
  }
}
