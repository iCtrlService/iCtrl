import React from 'react';
import {Chip, IconButton} from '@material-ui/core';
import {KeyboardArrowDown} from '@material-ui/icons';

import './index.css'

export default class Toolbar extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            pressed: new Set()
        };
    }

    handleChipClick = (key) => {
        const {onToolbarSendKey:sendKey} = this.props;
        const {pressed} = this.state
        switch (key) {
            case 'Ctrl':
            case '⌘':
            case 'Alt':
                if (!pressed.has(key)){
                    // previously not toggled
                    sendKey(key, true);
                    pressed.add(key)

                    const textarea = document.getElementsByTagName('textarea')[0]
                    const cancelAll = (_)=>{
                        setTimeout(()=>{
                            for (let pressedKey of pressed){
                            sendKey(pressedKey, false);
                        }
                        this.setState({pressed: new Set()})
                        textarea.removeEventListener('keydown', cancelAll, true)
                        },0)

                    }
                    textarea.removeEventListener('keydown', cancelAll, true)
                    textarea.addEventListener('keydown', cancelAll, true)
                } else {
                    // previously toggled
                    sendKey(key, false);
                    pressed.delete(key)
                }
                break;
            case 'Tab':
            case 'Esc':
            case 'Delete':
                sendKey(key)
                break;
            case 'Ctrl+Alt+Delete':
                this.props.onCtrlAltDelete()
                break;
            default:
                break;
        }
        this.setState({pressed: pressed})
    };

    render() {
        const {onToolbarHide:handleToolbarHide} = this.props;
        const {pressed} = this.state
        const keyList = [
                        {label: 'Ctrl'},
                        {label: '⌘'},
                        {label: 'Alt'},
                        {label: 'Tab'},
                        {label: 'Esc'},
                        {label: 'Delete'},
                    ];
        if (this.props.onCtrlAltDelete){
            keyList.push({label: 'Ctrl+Alt+Delete'})
        }
        return (
            <div id={'toolbar'}>
                <IconButton
                    style={{marginLeft:6}}
                    color={'info'}
                    onClick={handleToolbarHide}
                >
                    <KeyboardArrowDown/>
                </IconButton>
                {
                    keyList.map((item) => (
                        <Chip key={item.label}
                              label={item.label}
                              color="primary"
                              style={{
                              marginLeft:12}}
                              variant={pressed.has(item.label)?'filled':'outlined'}
                              onClick={()=>{this.handleChipClick(item.label)}}
                        />))}
            </div>
        );
    }
}