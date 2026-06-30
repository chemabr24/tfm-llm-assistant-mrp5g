import { Component } from '@angular/core';
import { ChatContainerComponent } from './components/chat-container/chat-container';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ChatContainerComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {}