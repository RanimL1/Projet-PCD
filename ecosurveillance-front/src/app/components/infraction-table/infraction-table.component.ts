import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Infraction } from '../../models/infraction.model';

@Component({
  selector: 'app-infraction-table',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './infraction-table.component.html',
  styleUrls: ['./infraction-table.component.css']
})
export class InfractionTableComponent {
  @Input() infractions: any[] = [];
  @Input() readOnly: boolean = false;
  @Output() edit = new EventEmitter<any>();
  @Output() delete = new EventEmitter<number>();
  @Output() changeStatus = new EventEmitter<number>();
  @Output() viewProofs = new EventEmitter<number>();

  getNomComplet(infraction: Infraction): string {
    if (infraction.nom || infraction.prenom) {
      return `${infraction.prenom || ''} ${infraction.nom || ''}`.trim();
    }
    return '-';
  }

  onEdit(infraction: any) {
    if (!this.readOnly) {
      this.edit.emit(infraction);
    }
  }

  onDelete(id: number) {
    if (!this.readOnly) {
      this.delete.emit(id);
    }
  }

  onChangeStatus(event: Event, id: number) {
    event.stopPropagation();
    this.changeStatus.emit(id);
  }

  openProofs(id: number): void {
    this.viewProofs.emit(id); // délègue au parent
  }
}

