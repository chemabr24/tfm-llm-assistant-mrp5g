import { Component } from '@angular/core';
import { ChatComponent } from '../chat/chat';

@Component({
  selector: 'app-chat-container',
  standalone: true,
  imports: [ChatComponent],
  templateUrl: './chat-container.html',
  styleUrl: './chat-container.scss'
})
export class ChatContainerComponent {}